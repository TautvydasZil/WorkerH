import json
import os
import time
from app import app
from seed import seed_database
from openapi_spec import OPENAPI_SPEC


def export_openapi_and_postman():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    # 1. Export OpenAPI JSON
    openapi_path = os.path.join(base_dir, 'openapi.json')
    with open(openapi_path, 'w', encoding='utf-8') as f:
        json.dump(OPENAPI_SPEC, f, ensure_ascii=False, indent=2)

    # 2. Export Postman Collection & Environment
    postman_dir = os.path.join(root_dir, 'postman')
    os.makedirs(postman_dir, exist_ok=True)

    def make_item(name, method, path, expected_status, body=None, extra_test_js=None):
        tests = [
            f"pm.test('Status code is {expected_status}', function () {{ pm.response.to.have.status({expected_status}); }});",
            "pm.test('Content-Type is application/json', function () { pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json'); });"
        ]
        if extra_test_js:
            tests.extend(extra_test_js)

        req = {
            "method": method,
            "header": [
                {"key": "Content-Type", "value": "application/json"},
                {"key": "Authorization", "value": "Basic YWRtaW46YWRtaW4xMjM="}
            ],
            "url": {
                "raw": "{{baseUrl}}" + path,
                "host": ["{{baseUrl}}"],
                "path": [p for p in path.strip('/').split('/') if p]
            }
        }
        if body is not None:
            req["body"] = {
                "mode": "raw",
                "raw": json.dumps(body, ensure_ascii=False, indent=2)
            }
        return {
            "name": name,
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "type": "text/javascript",
                        "exec": tests
                    }
                }
            ],
            "request": req
        }

    collection = {
        "info": {
            "_postman_id": "a7f9c120-b165-4000-8000-workerh202601",
            "name": "WorkerH REST API (1 Lab. darbas - 15 metodų + 404/400/422/201/200)",
            "description": "Pilna WorkerH REST API Postman kolekcija (15 hierarchinių API metodų: Project -> Task -> WorkHours bei klaidų kodų 404, 400, 422 demonstracija).",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:5000"},
            {"key": "created_project_id", "value": "1"},
            {"key": "created_task_id", "value": "1"},
            {"key": "created_hours_id", "value": "1"}
        ],
        "item": [
            {
                "name": "1. Projektai (1 lygmuo) ir Užduotys (2 lygmuo) ir Darbo laikas (3 lygmuo) — 15 API Metodų",
                "item": [
                    make_item(
                        "01. [GET] Gauti visų projektų sąrašą (200 OK)",
                        "GET", "/api/projects", 200,
                        extra_test_js=[
                            "pm.test('Grąžinamas projektų masyvas', function () { var j = pm.response.json(); pm.expect(j).to.be.an('array'); pm.expect(j.length).to.be.above(0); });"
                        ]
                    ),
                    make_item(
                        "02. [POST] Sukurti naują projektą (201 Created)",
                        "POST", "/api/projects", 201,
                        body={
                            "name": "Demonstracinis projektas (Postman)",
                            "address": "Studentų g. 50, Kaunas",
                            "latitude": 54.9039,
                            "longitude": 23.9578
                        },
                        extra_test_js=[
                            "var j = pm.response.json();",
                            "pm.collectionVariables.set('created_project_id', j.id);",
                            "pm.test('Projektas sukurtas su ID', function () { pm.expect(j.id).to.be.a('number'); pm.expect(j.name).to.eql('Demonstracinis projektas (Postman)'); });"
                        ]
                    ),
                    make_item(
                        "03. [GET] Gauti konkretų projektą pagal ID (200 OK)",
                        "GET", "/api/projects/{{created_project_id}}", 200,
                        extra_test_js=[
                            "pm.test('Grąžintas teisingas projektas', function () { var j = pm.response.json(); pm.expect(j.id).to.eql(Number(pm.collectionVariables.get('created_project_id'))); });"
                        ]
                    ),
                    make_item(
                        "04. [PUT] Atnaujinti projektą pagal ID (200 OK)",
                        "PUT", "/api/projects/{{created_project_id}}", 200,
                        body={
                            "name": "Atnaujintas demonstracinis projektas",
                            "address": "K. Baršausko g. 59, Kaunas"
                        },
                        extra_test_js=[
                            "pm.test('Projekto pavadinimas atnaujintas', function () { var j = pm.response.json(); pm.expect(j.name).to.eql('Atnaujintas demonstracinis projektas'); });"
                        ]
                    ),
                    make_item(
                        "05. [GET] Gauti projekto užduočių sąrašą (200 OK)",
                        "GET", "/api/projects/1/tasks", 200,
                        extra_test_js=[
                            "pm.test('Grąžinamas užduočių sąrašas', function () { var j = pm.response.json(); pm.expect(j).to.be.an('array'); });"
                        ]
                    ),
                    make_item(
                        "06. [POST] Sukurti naują užduotį projekte (201 Created)",
                        "POST", "/api/projects/{{created_project_id}}/tasks", 201,
                        body={
                            "title": "Serverinės spintos montavimas",
                            "description": "Sumontuoti 42U komutacinę spintą ir sujungti optinius kabelius",
                            "status": "in_progress"
                        },
                        extra_test_js=[
                            "var j = pm.response.json();",
                            "pm.collectionVariables.set('created_task_id', j.id);",
                            "pm.test('Užduotis sukurta', function () { pm.expect(j.id).to.be.a('number'); pm.expect(j.title).to.eql('Serverinės spintos montavimas'); });"
                        ]
                    ),
                    make_item(
                        "07. [GET] Gauti konkrečią projekto užduotį pagal ID (200 OK)",
                        "GET", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}", 200,
                        extra_test_js=[
                            "pm.test('Grąžinta teisinga užduotis', function () { var j = pm.response.json(); pm.expect(j.id).to.eql(Number(pm.collectionVariables.get('created_task_id'))); });"
                        ]
                    ),
                    make_item(
                        "08. [PUT] Atnaujinti projekto užduotį pagal ID (200 OK)",
                        "PUT", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}", 200,
                        body={
                            "title": "Serverinės spintos montavimas ir testavimas",
                            "status": "done"
                        },
                        extra_test_js=[
                            "pm.test('Užduotis atnaujinta', function () { var j = pm.response.json(); pm.expect(j.status).to.eql('done'); });"
                        ]
                    ),
                    make_item(
                        "09. [GET] Gauti projekto užduoties darbo laiko įrašų sąrašą (200 OK)",
                        "GET", "/api/projects/1/tasks/1/hours", 200,
                        extra_test_js=[
                            "pm.test('Grąžinamas darbo valandų sąrašas', function () { var j = pm.response.json(); pm.expect(j).to.be.an('array'); });"
                        ]
                    ),
                    make_item(
                        "10. [POST] Sukurti darbo laiko įrašą projekto užduočiai (201 Created)",
                        "POST", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}/hours", 201,
                        body={
                            "date": "2026-10-01",
                            "start_time": "08:00",
                            "end_time": "17:00",
                            "lunch_break": 60,
                            "notes": "Sumontuota komutacinė spinta ir patikrintas ryšys"
                        },
                        extra_test_js=[
                            "var j = pm.response.json();",
                            "pm.collectionVariables.set('created_hours_id', j.id);",
                            "pm.test('Darbo laiko įrašas sukurtas (8 val.)', function () { pm.expect(j.id).to.be.a('number'); pm.expect(j.hours).to.eql(8); });"
                        ]
                    ),
                    make_item(
                        "11. [GET] Gauti konkretų darbo laiko įrašą pagal ID (200 OK)",
                        "GET", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}/hours/{{created_hours_id}}", 200,
                        extra_test_js=[
                            "pm.test('Grąžintas teisingas darbo laiko įrašas', function () { var j = pm.response.json(); pm.expect(j.id).to.eql(Number(pm.collectionVariables.get('created_hours_id'))); });"
                        ]
                    ),
                    make_item(
                        "12. [PUT] Atnaujinti darbo laiko įrašą pagal ID (200 OK)",
                        "PUT", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}/hours/{{created_hours_id}}", 200,
                        body={
                            "date": "2026-10-01",
                            "start_time": "08:00",
                            "end_time": "16:30",
                            "lunch_break": 30,
                            "notes": "Atnaujintas komentaras ir pertraukos trukmė"
                        },
                        extra_test_js=[
                            "pm.test('Darbo laiko įrašas atnaujintas', function () { var j = pm.response.json(); pm.expect(j.end_time).to.eql('16:30'); pm.expect(j.lunch_break).to.eql(30); });"
                        ]
                    ),
                    make_item(
                        "13. [DELETE] Ištrinti darbo laiko įrašą (200 OK)",
                        "DELETE", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}/hours/{{created_hours_id}}", 200,
                        extra_test_js=[
                            "pm.test('Darbo laiko įrašas ištrintas', function () { var j = pm.response.json(); pm.expect(j).to.have.property('message'); });"
                        ]
                    ),
                    make_item(
                        "14. [DELETE] Ištrinti projekto užduotį (200 OK)",
                        "DELETE", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}", 200,
                        extra_test_js=[
                            "pm.test('Užduotis ištrinta', function () { var j = pm.response.json(); pm.expect(j).to.have.property('message'); });"
                        ]
                    ),
                    make_item(
                        "15. [DELETE] Ištrinti projektą (200 OK)",
                        "DELETE", "/api/projects/{{created_project_id}}", 200,
                        extra_test_js=[
                            "pm.test('Projektas ištrintas', function () { var j = pm.response.json(); pm.expect(j).to.have.property('message'); });"
                        ]
                    )
                ]
            },
            {
                "name": "2. Klaidų situacijų demonstravimas (404 Not Found, 400 Bad Request, 422 Unprocessable Entity)",
                "item": [
                    make_item(
                        "16. [404 Not Found] Kai projektas nerandamas",
                        "GET", "/api/projects/999999", 404,
                        extra_test_js=["pm.test('Grąžintas klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "17. [404 Not Found] Kai užduotis nerandama projekte",
                        "GET", "/api/projects/1/tasks/999999", 404,
                        extra_test_js=["pm.test('Grąžintas klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "18. [404 Not Found] Kai darbo laiko įrašas nerandamas",
                        "GET", "/api/projects/1/tasks/1/hours/999999", 404,
                        extra_test_js=["pm.test('Grąžintas klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "19. [400 Bad Request] Kai trūksta privalomų laukų kuriant projektą",
                        "POST", "/api/projects", 400,
                        body={},
                        extra_test_js=["pm.test('Grąžintas 400 klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "20. [400 Bad Request] Kai trūksta privalomų laukų kuriant darbo valandas",
                        "POST", "/api/projects/1/tasks/1/hours", 400,
                        body={"date": "2026-10-19"},
                        extra_test_js=["pm.test('Grąžintas 400 klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "21. [422 Unprocessable Entity] Kai projekto pavadinimas per trumpas arba koordinatės netinkamos",
                        "POST", "/api/projects", 422,
                        body={"name": "A", "latitude": 150.0},
                        extra_test_js=["pm.test('Grąžintas 422 validacijos klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "22. [422 Unprocessable Entity] Kai užduočiai nurodoma neegzistuojanti būsena",
                        "POST", "/api/projects/1/tasks", 422,
                        body={"title": "Testinė užduotis", "status": "nezinoma_busena"},
                        extra_test_js=["pm.test('Grąžintas 422 validacijos klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "23. [422 Unprocessable Entity] Kai darbo pabaigos laikas ankstesnis už pradžios laiką",
                        "POST", "/api/projects/1/tasks/1/hours", 422,
                        body={"date": "2026-10-19", "start_time": "17:00", "end_time": "08:00"},
                        extra_test_js=["pm.test('Grąžintas 422 validacijos klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    )
                ]
            }
        ]
    }

    coll_path = os.path.join(postman_dir, 'WorkerH_API.postman_collection.json')
    with open(coll_path, 'w', encoding='utf-8') as f:
        json.dump(collection, f, ensure_ascii=False, indent=2)

    env_data = {
        "id": "b8e0d231-c276-4111-9111-workerhenv01",
        "name": "WorkerH Local Environment",
        "values": [
            {"key": "baseUrl", "value": "http://localhost:5000", "enabled": True}
        ],
        "_postman_variable_scope": "environment"
    }
    env_path = os.path.join(postman_dir, 'WorkerH_Local.postman_environment.json')
    with open(env_path, 'w', encoding='utf-8') as f:
        json.dump(env_data, f, ensure_ascii=False, indent=2)


def run_demo_tests():
    start_ts = time.time()
    with app.app_context():
        seed_database(reset=False)

    client = app.test_client()
    headers = {'Authorization': 'Basic YWRtaW46YWRtaW4xMjM='}

    print("=" * 75)
    print("WorkerH REST API — 15 METODŲ IR KLAIDŲ KODŲ DEMONSTRACIJA")
    print("=" * 75)

    # 1. GET /api/projects
    r = client.get('/api/projects', headers=headers)
    assert r.status_code == 200 and 'application/json' in r.content_type
    print(f"[01/15] GET    /api/projects                                    -> {r.status_code} OK ({len(r.get_json())} projektai)")

    # 2. POST /api/projects
    r = client.post('/api/projects', json={
        'name': 'Demonstracinis projektas',
        'address': 'Studentų g. 50, Kaunas',
        'latitude': 54.9039,
        'longitude': 23.9578
    }, headers=headers)
    assert r.status_code == 201
    proj_id = r.get_json()['id']
    print(f"[02/15] POST   /api/projects                                    -> {r.status_code} Created (id={proj_id})")

    # 3. GET /api/projects/<id>
    r = client.get(f'/api/projects/{proj_id}', headers=headers)
    assert r.status_code == 200 and r.get_json()['id'] == proj_id
    print(f"[03/15] GET    /api/projects/{proj_id:<34} -> {r.status_code} OK")

    # 4. PUT /api/projects/<id>
    r = client.put(f'/api/projects/{proj_id}', json={
        'name': 'Atnaujintas demonstracinis projektas',
        'address': 'K. Baršausko g. 59, Kaunas'
    }, headers=headers)
    assert r.status_code == 200 and r.get_json()['name'] == 'Atnaujintas demonstracinis projektas'
    print(f"[04/15] PUT    /api/projects/{proj_id:<34} -> {r.status_code} OK")

    # 5. GET /api/projects/<id>/tasks
    r = client.get('/api/projects/1/tasks', headers=headers)
    assert r.status_code == 200
    print(f"[05/15] GET    /api/projects/1/tasks                            -> {r.status_code} OK ({len(r.get_json())} užduotys)")

    # 6. POST /api/projects/<id>/tasks
    r = client.post(f'/api/projects/{proj_id}/tasks', json={
        'title': 'Serverinės spintos montavimas',
        'description': 'Komutacinės spintos montavimas',
        'status': 'in_progress'
    }, headers=headers)
    assert r.status_code == 201
    task_id = r.get_json()['id']
    print(f"[06/15] POST   /api/projects/{proj_id}/tasks                           -> {r.status_code} Created (id={task_id})")

    # 7. GET /api/projects/<id>/tasks/<task_id>
    r = client.get(f'/api/projects/{proj_id}/tasks/{task_id}', headers=headers)
    assert r.status_code == 200 and r.get_json()['id'] == task_id
    print(f"[07/15] GET    /api/projects/{proj_id}/tasks/{task_id:<26} -> {r.status_code} OK")

    # 8. PUT /api/projects/<id>/tasks/<task_id>
    r = client.put(f'/api/projects/{proj_id}/tasks/{task_id}', json={
        'title': 'Serverinės spintos montavimas ir testavimas',
        'status': 'done'
    }, headers=headers)
    assert r.status_code == 200 and r.get_json()['status'] == 'done'
    print(f"[08/15] PUT    /api/projects/{proj_id}/tasks/{task_id:<26} -> {r.status_code} OK")

    # 9. GET /api/projects/<id>/tasks/<task_id>/hours
    r = client.get('/api/projects/1/tasks/1/hours', headers=headers)
    assert r.status_code == 200
    print(f"[09/15] GET    /api/projects/1/tasks/1/hours                    -> {r.status_code} OK ({len(r.get_json())} įrašai)")

    # 10. POST /api/projects/<id>/tasks/<task_id>/hours
    r = client.post(f'/api/projects/{proj_id}/tasks/{task_id}/hours', json={
        'date': '2026-10-01',
        'start_time': '08:00',
        'end_time': '17:00',
        'lunch_break': 60,
        'notes': 'Atliktas montavimas'
    }, headers=headers)
    assert r.status_code == 201
    hours_id = r.get_json()['id']
    print(f"[10/15] POST   /api/projects/{proj_id}/tasks/{task_id}/hours                    -> {r.status_code} Created (id={hours_id})")

    # 11. GET /api/projects/<id>/tasks/<task_id>/hours/<hours_id>
    r = client.get(f'/api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id}', headers=headers)
    assert r.status_code == 200 and r.get_json()['id'] == hours_id
    print(f"[11/15] GET    /api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id:<18} -> {r.status_code} OK")

    # 12. PUT /api/projects/<id>/tasks/<task_id>/hours/<hours_id>
    r = client.put(f'/api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id}', json={
        'date': '2026-10-01',
        'start_time': '08:00',
        'end_time': '16:30',
        'lunch_break': 30,
        'notes': 'Atnaujintas darbo įrašas'
    }, headers=headers)
    assert r.status_code == 200 and r.get_json()['end_time'] == '16:30'
    print(f"[12/15] PUT    /api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id:<18} -> {r.status_code} OK")

    # 13. DELETE /api/projects/<id>/tasks/<task_id>/hours/<hours_id>
    r = client.delete(f'/api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id}', headers=headers)
    assert r.status_code == 200
    print(f"[13/15] DELETE /api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id:<18} -> {r.status_code} OK")

    # 14. DELETE /api/projects/<id>/tasks/<task_id>
    r = client.delete(f'/api/projects/{proj_id}/tasks/{task_id}', headers=headers)
    assert r.status_code == 200
    print(f"[14/15] DELETE /api/projects/{proj_id}/tasks/{task_id:<26} -> {r.status_code} OK")

    # 15. DELETE /api/projects/<id>
    r = client.delete(f'/api/projects/{proj_id}', headers=headers)
    assert r.status_code == 200
    print(f"[15/15] DELETE /api/projects/{proj_id:<34} -> {r.status_code} OK")

    print("-" * 75)
    print("PAPILDOMI SCENARIJAI (404, 400, 422):")

    # 404 tests
    r404_p = client.get('/api/projects/999999', headers=headers)
    assert r404_p.status_code == 404
    print(f"[404]   GET    /api/projects/999999                             -> {r404_p.status_code} Not Found ({r404_p.get_json()['error']})")

    r404_t = client.get('/api/projects/1/tasks/999999', headers=headers)
    assert r404_t.status_code == 404
    print(f"[404]   GET    /api/projects/1/tasks/999999                     -> {r404_t.status_code} Not Found ({r404_t.get_json()['error']})")

    # 400 tests
    r400 = client.post('/api/projects', json={}, headers=headers)
    assert r400.status_code == 400
    print(f"[400]   POST   /api/projects (tuščias payload)                  -> {r400.status_code} Bad Request ({r400.get_json()['error']})")

    # 422 tests
    r422_p = client.post('/api/projects', json={'name': 'A'}, headers=headers)
    assert r422_p.status_code == 422
    print(f"[422]   POST   /api/projects (per trumpas pavadinimas)          -> {r422_p.status_code} Unprocessable ({r422_p.get_json()['error']})")

    r422_h = client.post('/api/projects/1/tasks/1/hours', json={
        'date': '2026-10-19', 'start_time': '17:00', 'end_time': '08:00'
    }, headers=headers)
    assert r422_h.status_code == 422
    print(f"[422]   POST   /api/projects/1/tasks/1/hours (neigiamos val.)   -> {r422_h.status_code} Unprocessable ({r422_h.get_json()['error']})")

    elapsed = time.time() - start_ts
    print("=" * 75)
    print(f"VISI 15 API METODŲ IR KLAIDŲ TESTAI SĖKMINGAI PRAĖJO PER {elapsed:.2f} s!")
    print("=" * 75)


if __name__ == '__main__':
    export_openapi_and_postman()
    run_demo_tests()
