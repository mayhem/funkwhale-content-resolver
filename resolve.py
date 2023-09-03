#!/usr/bin/env python3

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, InternalServerError
import psycopg2
import psycopg2.extras

from lb_content_resolver.fuzzy_index import FuzzyIndex

DB_CONNECT = "postgresql://postgres@funkwhale_postgres_1:5432/postgres"

app = Flask(__name__)

def build_track_index():

    index = FuzzyIndex("")

    query = """SELECT mt.id
                    , mt.title AS recording_name
                    , ma.name AS artist_name
                 FROM music_track mt
                 JOIN music_artist ma
                   ON mt.artist_id = ma.id"""

    artist_recording_data = []
    with psycopg2.connect(DB_CONNECT) as conn:    
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:
            curs.execute(query)

            print(f"Fetch {curs.rowcount} tracks fetched.")
            for row in curs.fetchall():
                artist_recording_data.append((row["artist_name"], row["recording_name"], row["id"]))

    index.build(artist_recording_data)
    recording_id_index = { ar[2] : (ar[0], ar[1]) for ar in artist_recording_data }

    return index, recording_id_index

def lookup_tracks(index, query_data):
    return index.search(query_data)


def create_funkwhale_playlist(user_id, matched_tracks, jspf):

    with psycopg2.connect(DB_CONNECT) as conn:    
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as curs:

            curs.execute("""INSERT INTO playlists_playlist (name, user_id, privacy_level, creation_date, modification_date)
                                 VALUES (%s, %s, %s, now(), now())
                              RETURNING id""", (jspf["playlist"]["title"], user_id, "instance"))
            playlist_id = curs.fetchone()["id"]

            for i, track in enumerate(matched_tracks):
                curs.execute("""INSERT INTO playlists_playlisttrack (playlist_id, track_id, creation_date, index)
                                     VALUES (%s, %s, now(), %s)""", (playlist_id, int(track["recording_id"]), i))

            conn.commit()


@app.route("/resolve", methods=["POST"])
def resolve():
    jspf = request.json

    user_id = request.args.get("user_id", None)
    if user_id is None:
        raise BadRequest("Parameter user_id must be specified.")

    query_data = []
    for track in jspf["playlist"]["track"]:
        query_data.append({ "recording_name": track["title"], "artist_name": track["creator"]})

    try:
        index, recording_id_index = build_track_index()
        candidate_tracks = lookup_tracks(index, query_data)
        matched_tracks = []
        for i, track in enumerate(candidate_tracks):
            print("QUERY %-50s %-50s" % (query_data[i]['recording_name'][:49], query_data[i]['artist_name'][:49]))
            print("  HIT %-50s %-50s %d%%\n" % (recording_id_index[track["recording_id"]][1][:49],
                                                recording_id_index[track["recording_id"]][0][:49], int(100 * track['confidence'])))
            if track['confidence'] > .7:
                matched_tracks.append(track)

        create_funkwhale_playlist(user_id, matched_tracks, jspf)
    except Exception as err:
        raise InternalServerError(f"Could not build or resolve playlist: {err}")

    return jsonify({ "status": "ok"})
