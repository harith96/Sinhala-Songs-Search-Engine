from datetime import datetime
from flask import Flask, jsonify, request, send_file
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from flask_cors import CORS
import json

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
    keyword = request.args.get('q')

    body = {}

    body = {
        "query": {
            "multi_match": {
                "query": keyword,
                "type": "bool_prefix",
                "fields": ["title_si*", "artist_si*", "lyrics", "writer*", "composer_si*", "genre_si*"],
                "_source": [ "title_si", "writer", "artist_si", "composer_si", "genre_si", "n_visits", "lyrics" ]
            }
        }
    }
    res = es.search(index="songs", doc_type="_doc", body=body)
    print(res['hits']['hits'])

    return jsonify(res['hits']['hits'])

if __name__ == "__main__":
    app.run(debug=True)