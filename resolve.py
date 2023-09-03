#!/usr/bin/env python3

import psycopg2

from lb_content_resolver.fuzzy_index import FuzzyIndex


DB_CONNECT = "postgresql://postgres@funkwhale-postgres-1:5432/postgres"


def resolve_jspf_playlist(jspf_file: str):

    index = FuzzyIndex("")

    query = """SELECT mt.id
                    , mt.title AS recording_name
                    , ma.name AS artist_name
                 FROM music_track mt
                 JOIN music_artist ma
                   ON mt.artist_id = ma.id"""

    artist_recording_data = []
    with psycopg2.connect(DB_CONNECT) as conn:    
        with conn.cursor() as curs:
            curs.execute(query)

            print(f"Fetch {curs.rowcount} tracks fetched.")
            for row in curs.fetchall():
                artist_recording_data.append((row["recording_name"], row["artist_name"], row["id"]))

    index.build(artist_recording_data)
    print("Index built.")
  


if __name__ == "__main__":
    resolve_jspf_playlist("test.jspf")
