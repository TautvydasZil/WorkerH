import json
import os
import time
from app import app
from seed import seed_database
from openapi_spec import OPENAPI_SPEC
from models import Project, Task, HoursLogged


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
            f"pm.test('Status code is {expected_status}', function () {{ pm.response.to.have.status({expected_status}); }});"
        ]
        if expected_status != 204:
            tests.append(
                "pm.test('Content-Type is application/json', function () { pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json'); });"
            )
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
                "path": [p for p in path.split('?')[0].strip('/').split('/') if p]
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
            "name": "WorkerH REST API (1 Lab. darbas - 15 metodų + Puslapiavimas, Filtravimas, HATEOAS, 404/400/422/201/204)",
            "description": "Pilna WorkerH REST API Postman kolekcija (15 hierarchinių API metodų: Project -> Task -> WorkHours, puslapiavimas, filtravimas, HATEOAS, sudėtinis resursas ir klaidų kodai).",
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
                "name": "1. Projektai (1 lygmuo), Užduotys (2 lygmuo), Darbo laikas (3 lygmuo) — 15 API Metodų",
                "item": [
                    make_item(
                        "01. [GET] Gauti visų projektų sąrašą + HATEOAS (200 OK)",
                        "GET", "/api/projects", 200,
                        extra_test_js=[
                            "pm.test('Bent 5 projektai ir yra _links (HATEOAS)', function () { var j = pm.response.json(); pm.expect(j).to.be.an('array'); pm.expect(j.length).to.be.at.least(5); pm.expect(j[0]).to.have.property('_links'); });"
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
                            "pm.test('Projektas sukurtas su ID ir _links', function () { pm.expect(j.id).to.be.a('number'); pm.expect(j).to.have.property('_links'); });"
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
                            "pm.test('Grąžinamas užduočių sąrašas su _links', function () { var j = pm.response.json(); pm.expect(j).to.be.an('array'); pm.expect(j[0]).to.have.property('_links'); });"
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
                            "pm.test('Grąžinamas darbo valandų sąrašas su _links', function () { var j = pm.response.json(); pm.expect(j).to.be.an('array'); pm.expect(j[0]).to.have.property('_links'); });"
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
                        "13. [DELETE] Ištrinti darbo laiko įrašą (204 No Content)",
                        "DELETE", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}/hours/{{created_hours_id}}", 204
                    ),
                    make_item(
                        "14. [DELETE] Ištrinti projekto užduotį (204 No Content)",
                        "DELETE", "/api/projects/{{created_project_id}}/tasks/{{created_task_id}}", 204
                    ),
                    make_item(
                        "15. [DELETE] Ištrinti projektą (204 No Content)",
                        "DELETE", "/api/projects/{{created_project_id}}", 204
                    )
                ]
            },
            {
                "name": "2. Puslapiavimas, Filtravimas, HATEOAS ir Sudėtinis resursas (Summary)",
                "item": [
                    make_item(
                        "16. [Puslapiavimas] GET /api/projects?page=1&per_page=3&envelope=1",
                        "GET", "/api/projects?page=1&per_page=3&envelope=1", 200,
                        extra_test_js=[
                            "pm.test('Puslapiavimas grąžina 3 įrašus ir _links', function () { var j = pm.response.json(); pm.expect(j.items.length).to.eql(3); pm.expect(j.pagination.per_page).to.eql(3); pm.expect(j).to.have.property('_links'); });"
                        ]
                    ),
                    make_item(
                        "17. [Filtravimas] GET /api/projects?is_completed=false&search=Kauno",
                        "GET", "/api/projects?is_completed=false&search=Kauno", 200,
                        extra_test_js=[
                            "pm.test('Filtravimas pagal būseną ir paiešką veikia', function () { var j = pm.response.json(); pm.expect(j.length).to.be.above(0); pm.expect(j[0].is_completed).to.eql(false); });"
                        ]
                    ),
                    make_item(
                        "18. [Sudėtinis resursas iš 3 esybių] GET /api/projects/1/summary",
                        "GET", "/api/projects/1/summary", 200,
                        extra_test_js=[
                            "pm.test('Sudėtinis resursas turi project, statistics ir tasks_breakdown', function () { var j = pm.response.json(); pm.expect(j).to.have.property('project'); pm.expect(j).to.have.property('statistics'); pm.expect(j).to.have.property('tasks_breakdown'); });"
                        ]
                    )
                ]
            },
            {
                "name": "3. Klaidų situacijų demonstravimas (404 Not Found, 400 Bad Request, 422 Unprocessable Entity)",
                "item": [
                    make_item(
                        "19. [404 Not Found] Kai projektas nerandamas",
                        "GET", "/api/projects/999999", 404,
                        extra_test_js=["pm.test('Grąžintas klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "20. [404 Not Found] Kai užduotis nerandama projekte",
                        "GET", "/api/projects/1/tasks/999999", 404,
                        extra_test_js=["pm.test('Grąžintas klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "21. [404 Not Found] Kai darbo laiko įrašas nerandamas",
                        "GET", "/api/projects/1/tasks/1/hours/999999", 404,
                        extra_test_js=["pm.test('Grąžintas klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "22. [400 Bad Request] Kai trūksta privalomų laukų kuriant projektą",
                        "POST", "/api/projects", 400,
                        body={},
                        extra_test_js=["pm.test('Grąžintas 400 klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "23. [400 Bad Request] Kai trūksta privalomų laukų kuriant darbo valandas",
                        "POST", "/api/projects/1/tasks/1/hours", 400,
                        body={"date": "2026-10-19"},
                        extra_test_js=["pm.test('Grąžintas 400 klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "24. [422 Unprocessable Entity] Kai projekto pavadinimas per trumpas arba koordinatės netinkamos",
                        "POST", "/api/projects", 422,
                        body={"name": "A", "latitude": 150.0},
                        extra_test_js=["pm.test('Grąžintas 422 validacijos klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "25. [422 Unprocessable Entity] Kai užduočiai nurodoma neegzistuojanti būsena",
                        "POST", "/api/projects/1/tasks", 422,
                        body={"title": "Testinė užduotis", "status": "nezinoma_busena"},
                        extra_test_js=["pm.test('Grąžintas 422 validacijos klaidos pranešimas', function () { pm.expect(pm.response.json()).to.have.property('error'); });"]
                    ),
                    make_item(
                        "26. [422 Unprocessable Entity] Kai darbo pabaigos laikas ankstesnis už pradžios laiką",
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
        p_count = Project.query.count()
        t_count = Task.query.count()
        h_count = HoursLogged.query.count()
        assert p_count >= 5 and t_count >= 5 and h_count >= 5, "Kiekvienoje lentelėje turi būti bent 5 įrašai!"

    client = app.test_client()
    headers = {'Authorization': 'Basic YWRtaW46YWRtaW4xMjM='}

    print("=" * 78)
    print("WorkerH REST API — 15 METODŲ, PUSLAPIAVIMO, FILTRAVIMO, HATEOAS IR KLAIDŲ TESTAS")
    print(f"DB būsena: Projektai={p_count} (>=5), Užduotys={t_count} (>=5), Darbo valandos={h_count} (>=5)")
    print("=" * 78)

    # 1. GET /api/projects
    r = client.get('/api/projects', headers=headers)
    assert r.status_code == 200 and 'application/json' in r.content_type
    assert '_links' in r.get_json()[0]
    print(f"[01/15] GET    /api/projects                                    -> {r.status_code} OK ({len(r.get_json())} projektai, HATEOAS _links)")

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
    assert r.status_code == 200 and '_links' in r.get_json()[0]
    print(f"[05/15] GET    /api/projects/1/tasks                            -> {r.status_code} OK ({len(r.get_json())} užduotys, HATEOAS _links)")

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
    assert r.status_code == 200 and '_links' in r.get_json()[0]
    print(f"[09/15] GET    /api/projects/1/tasks/1/hours                    -> {r.status_code} OK ({len(r.get_json())} įrašai, HATEOAS _links)")

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
    print(f"[10/15] POST   /api/projects/{proj_id}/tasks/{task_id}/hours                  -> {r.status_code} Created (id={hours_id})")

    # 11. GET /api/projects/<id>/tasks/<task_id>/hours/<hours_id>
    r = client.get(f'/api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id}', headers=headers)
    assert r.status_code == 200 and r.get_json()['id'] == hours_id
    print(f"[11/15] GET    /api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id:<17} -> {r.status_code} OK")

    # 12. PUT /api/projects/<id>/tasks/<task_id>/hours/<hours_id>
    r = client.put(f'/api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id}', json={
        'date': '2026-10-01',
        'start_time': '08:00',
        'end_time': '16:30',
        'lunch_break': 30,
        'notes': 'Atnaujintas darbo įrašas'
    }, headers=headers)
    assert r.status_code == 200 and r.get_json()['end_time'] == '16:30'
    print(f"[12/15] PUT    /api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id:<17} -> {r.status_code} OK")

    # 13. DELETE /api/projects/<id>/tasks/<task_id>/hours/<hours_id>
    r = client.delete(f'/api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id}', headers=headers)
    assert r.status_code == 204
    print(f"[13/15] DELETE /api/projects/{proj_id}/tasks/{task_id}/hours/{hours_id:<17} -> {r.status_code} No Content")

    # 14. DELETE /api/projects/<id>/tasks/<task_id>
    r = client.delete(f'/api/projects/{proj_id}/tasks/{task_id}', headers=headers)
    assert r.status_code == 204
    print(f"[14/15] DELETE /api/projects/{proj_id}/tasks/{task_id:<26} -> {r.status_code} No Content")

    # 15. DELETE /api/projects/<id>
    r = client.delete(f'/api/projects/{proj_id}', headers=headers)
    assert r.status_code == 204
    print(f"[15/15] DELETE /api/projects/{proj_id:<34} -> {r.status_code} No Content")

    print("-" * 78)
    print("PAPILDOMI REIKALAVIMAI (Puslapiavimas, Filtravimas, Sudėtinis resursas, 404/400/422):")

    # Pagination
    r_page = client.get('/api/projects?page=1&per_page=3&envelope=1', headers=headers)
    assert r_page.status_code == 200 and len(r_page.get_json()['items']) == 3
    print(f"[PAGE]  GET    /api/projects?page=1&per_page=3&envelope=1       -> {r_page.status_code} OK (grąžinti 3 iš {r_page.get_json()['pagination']['total']})")

    # Filtering
    r_filt = client.get('/api/projects?is_completed=false&search=Kauno', headers=headers)
    assert r_filt.status_code == 200 and len(r_filt.get_json()) >= 1
    print(f"[FILT]  GET    /api/projects?is_completed=false&search=Kauno    -> {r_filt.status_code} OK (rasta: {len(r_filt.get_json())})")

    # Composite resource (Project + Task + HoursLogged)
    r_sum = client.get('/api/projects/1/summary', headers=headers)
    assert r_sum.status_code == 200 and 'statistics' in r_sum.get_json() and 'tasks_breakdown' in r_sum.get_json()
    print(f"[COMP]  GET    /api/projects/1/summary (iš 3 esybių)            -> {r_sum.status_code} OK (viso val.: {r_sum.get_json()['statistics']['total_hours_logged']})")

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
    print("=" * 78)
    print(f"VISI 15 API METODŲ SĖKMINGAI PATIKRINTI PER {elapsed:.2f} s!")
    print("=" * 78)


if __name__ == '__main__':
    export_openapi_and_postman()
    run_demo_tests()
