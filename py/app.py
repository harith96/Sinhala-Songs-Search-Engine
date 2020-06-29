
import sys
sys.path.append('../sinling')
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from flask_cors import CORS
import json
import re
from sinling import word_splitter

es = Elasticsearch()

app = Flask(__name__, static_url_path='')
CORS(app)

@app.route('/', methods=['GET'])
def index():
    return send_file('templates/index.html')


@app.route('/insert_data', methods=['POST'])
def insert_data():
    if es.indices.exists(index="songs"):
        data = []
        with open('lyrics_.json', encoding="utf-8") as json_file:
            data = json.load(json_file)
        result = bulk(es, data)
        return jsonify(result), 201
    else:
        return jsonify({"error":"Please create song index with custom mappings first using settings.json"}), 404

@app.route('/search', methods=['GET'])
def search():
    keywords = request.args.get('q')

    body = build_query_body(keywords)

    
    res = es.search(index="songs", doc_type="_doc", body=body)
    # print(res['hits']['hits'])

    return jsonify(res['hits']['hits'])
    # return "abc"


def build_query_body(keywords):
    composer_list = [ 'සංගීතමය', 'සංගීතවත්','අධ්‍යක්ෂණය', 'සංගීත']
    artist_list = ['කීව', 'කී', 'ගායනා කරන', 'ගයන', 'ගායනා','‌ගේ', 'හඩින්', 'කියනා', 'කිව්ව', 'කිව්', 'කිව', 'ගායනය', 'ගායනා කළා', 'ගායනා කල', 'ගැයූ']
    writer_list = ['ලියා', 'ලියූ', 'ලිව්ව', 'ලිව්', 'රචනා',  'ලියා ඇති', 'රචිත', 'ලියන ලද','ලියන', 'හදපු', 'පද', 'රචනය', 'හැදූ', 'හැදුව', 'ලියන', 'ලියන්න','ලීව', 'ලියපු', 'ලියා ඇත', 'ලිඛිත']
    popular_list = ['සුපිරි', 'නියම', 'පට්ට','ඉහළම', 'හොඳ', 'හොඳම', 'එලකිරි', 'එළකිරි', 'සුප්පර්', 'සුප්රකට', 'ඉහල',  'වැඩිපුර', 'වැඩිපුරම', 'සුප්‍රකට', 'ජනප්රිය', 'ජනප්රියම', 'ජනප්‍රිය', 'ජනප්‍රියම', 'ප්‍රකට', 'ප්‍රසිද්ධ', 'ප්‍රසිද්ධම', 'ප්‍රකටම']
    drop_list = ["ගීත", "ගී", "සින්දු"]

    is_composer_query = False
    is_artist_query = False
    is_writer_query = False
    is_title_query = True

    pre_str = ""
    number=-1

    words = keywords.split(" ")
    is_popular_query = False
    for word in words:
        if(word in composer_list):
            is_composer_query = True
        elif(word in artist_list):
            is_artist_query = True
        elif(word in writer_list):
            is_writer_query = True
        elif(word in popular_list):
            is_popular_query = True
        elif(word.isdigit()):
            number = word
        else:
            pre_str+= word + " "

    composer_field = "composer_si*"
    artist_field = "artist_si*"
    writer_field = "writer*"
    title_field = "title_si*"
    lyrics_field = "lyrics"
    genre_field = "genre_si"

    query_str = ""

    if(is_composer_query or is_artist_query or is_popular_query or is_writer_query):
        is_title_query = False
        for word in pre_str.split(" "):
            if (not(word in drop_list)):
                query_str+= word + " "
    else:
        query_str = pre_str

    if(is_composer_query):
        composer_field += "^4"

    if(is_artist_query):
        artist_field += "^4"
    
    if(is_writer_query):
        writer_field += "^4"

    if(is_title_query):
        title_field += "^4"

    fields = [composer_field, artist_field, writer_field, title_field, lyrics_field, genre_field]
    if(is_popular_query):
        if(number == -1):
            number == 50

        if(len(query_str.strip()) == 0):
            body = {
                "sort": [{
                    "n_visits": {
                        "order": "desc"
                        }
                    }
                ],
                "size": number
            }
        else:
            body = {
                "query": {
                    "query_string": {
                        "query": query_str,
                        "type": "bool_prefix",
                        "fields": fields,
                        "fuzziness": "AUTO",
                        "analyze_wildcard": True
                    }
                },
                "sort": [{
                    "n_visits": {
                        "order": "desc"
                        }
                    }
                ],
                "size": number
            }
    else:
        body = {
            "query": {
                "query_string": {
                    "query": query_str,
                    "type": "bool_prefix",
                    "fields":fields,
                }
            }
        }
    return body

if __name__ == "__main__":
    app.run(debug=True)