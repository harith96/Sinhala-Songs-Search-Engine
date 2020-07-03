import sys
sys.path.append("E:\projects\IR\sinhala-song-search-engine\sinling")
from sinling import word_splitter, SinhalaTokenizer
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from flask_cors import CORS
from langdetect import detect
import json
import re

es = Elasticsearch()
tokenizer = SinhalaTokenizer()

app = Flask(__name__, static_url_path='')
CORS(app)

@app.route('/', methods=['GET'])
def index():
    return send_file('templates/index.html')


@app.route('/insert_data', methods=['POST'])
def insert_data():
    if es.indices.exists(index="songs"):
        data = []
        with open('E:\projects\IR\sinhala-song-search-engine\py\lyrics_.json', encoding="utf-8") as json_file:
            data = json.load(json_file)
        result = bulk(es, data)
        return jsonify(result), 201
    else:
        return jsonify({"error":"Please create song index with custom mappings first using settings.json"}), 404

@app.route('/search', methods=['GET'])
def search():
    keywords = request.args.get('q')

    body = build_query_body(keywords)
    print(body)
    
    res = es.search(index="songs", doc_type="_doc", body=body)
    # print(res['hits']['hits'])

    return jsonify(res['hits']['hits'])
    
    # return "abc"

def build_query_body(keywords):
    body ={}
    if(isEnglish(keywords)):
        body = build_english_query_body(keywords)
    else:
        body = build_sinhala_query_body(keywords)
    return body

def build_english_query_body(keywords):
    return {
            "query": {
                "query_string": {
                    "query": keywords,
                    "type": "bool_prefix",
                    "fields":["composer", "artist", "title_en","genre"],
                    "fuzziness": "AUTO",
                }
            }
        }

def build_sinhala_query_body(keywords):
    composer_list = [ 'සංගීතමය', 'සංගීතවත්','අධ්‍යක්ෂණය', 'සංගීත']
    artist_list = ['කීව', 'කී', 'ගායනා', 'ගයන', 'ගායනා','‌ගේ', 'හඩින්', 'කියනා', 'කිව්ව', 'කිව්', 'කිව', 'ගායනය', 'ගායනා', 'ගැයූ']
    writer_list = ['ලියා', 'ලියූ', 'ලිව්ව', 'ලිව්', 'රචනා',  'ලියා', 'රචිත', 'ලියන','ලියන', 'හදපු', 'පද', 'රචනය', 'හැදූ', 'හැදුව', 'ලියන', 'ලියන්න','ලීව', 'ලියපු', 'ලියා', 'ලිඛිත']
    popular_list = ['සුපිරි', 'නියම', 'පට්ට','ඉහළම', 'හොඳ', 'හොඳම', 'එලකිරි', 'එළකිරි', 'සුප්පර්', 'සුප්රකට', 'ඉහල',  'වැඩිපුර', 'වැඩිපුරම', 'සුප්‍රකට', 'ජනප්රිය', 'ජනප්රියම', 'ජනප්‍රිය', 'ජනප්‍රියම', 'ප්‍රකට', 'ප්‍රසිද්ධ', 'ප්‍රසිද්ධම', 'ප්‍රකටම']
    drop_list = ["ගීත", "ගී", "සින්දු"]

    is_composer_query = False
    is_artist_query = False
    is_writer_query = False
    is_title_query = True

    pre_str = ""
    number= 10

    words = tokenizer.tokenize(keywords)
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
            pre_str+= word + "~ "

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
            if (not(word.split("~")[0] in drop_list)):
                query_str+= word + " "
    else:
        query_str = pre_str

    fields = []
    if(is_composer_query):
        if(is_popular_query):
            fields.append(composer_field)
        else:
            composer_field += "^4"
        

    if(is_artist_query):
        if(is_popular_query):
            fields.append(artist_field)
        else:
            artist_field += "^4"
    
    if(is_writer_query):
        if(is_popular_query):
            fields.append(writer_field)
        else:
            writer_field += "^4"

    if(is_title_query):
        if(is_popular_query):
            fields.append(title_field)
        else:
            title_field += "^4"

    
    if(is_popular_query):
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
                        "fuzziness":3,
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
        fields = [composer_field, artist_field, writer_field, title_field, lyrics_field, genre_field]
        body = {
            "query": {
                "query_string": {
                    "query": query_str,
                    "type": "bool_prefix",
                    "fields":fields,
                    "fuzziness": 3,
                }
            }
        }
    # print(fields)
    return body

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

if __name__ == "__main__":
    app.run(debug=True)