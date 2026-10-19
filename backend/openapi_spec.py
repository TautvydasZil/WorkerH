OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "WorkerH REST API",
        "version": "1.0.0",
        "description": (
            "Įmonės darbuotojų darbo laiko apskaitos, projektų užduočių valdymo bei atostogų ir nedarbingumo "
            "tvarkymo REST API sąsaja.\n\n"
            "Realizuotas trijų lygmenų hierarchinis ryšys (15 pagrindinių CRUD API metodų):\n"
            "1. **Projektas (Project)** (`/api/projects`, `/api/projects/{project_id}`)\n"
            "2. **Užduotis (Task)** (`/api/projects/{project_id}/tasks`, `/api/projects/{project_id}/tasks/{task_id}`)\n"
            "3. **Darbo laikas (WorkHours)** (`/api/projects/{project_id}/tasks/{task_id}/hours`, "
            "`/api/projects/{project_id}/tasks/{task_id}/hours/{entry_id}`)"
        ),
        "contact": {
            "name": "Tautvydas Žilinskas"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Vietinis kūrimo ir demonstravimo serveris"
        }
    ],
    "tags": [
        {"name": "1. Projektai (Project - 1 lygmuo)", "description": "Projektų CRUD operacijos (5 metodai)"},
        {"name": "2. Užduotys (Task - 2 lygmuo)", "description": "Projektui priskirtų užduočių CRUD operacijos (5 metodai)"},
        {"name": "3. Darbo laikas (WorkHours - 3 lygmuo)", "description": "Projekto užduočiai priskirtų darbo laiko įrašų CRUD operacijos (5 metodai)"},
        {"name": "Autentifikacija (Auth)", "description": "Prisijungimas, atsijungimas, registracija, slaptažodžio atkūrimas"},
        {"name": "Darbo valandos (Plokšti maršrutai)", "description": "Bendrieji darbo laiko įrašų maršrutai"},
        {"name": "Atostogos ir nedarbingumas (Leave)", "description": "Atostogų ir nedarbingumo prašymų valdymas"},
        {"name": "Naudotojai ir pakvietimai (Users & Invites)", "description": "Naudotojų paskyrų ir el. pašto pakvietimų valdymas"}
    ],
    "components": {
        "securitySchemes": {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "session",
                "description": "Sesijos slapukas, gaunamas prisijungus per POST /api/auth/login"
            },
            "basicAuth": {
                "type": "http",
                "scheme": "basic",
                "description": "HTTP Basic autentifikacija (pvz. admin / admin123)"
            }
        },
        "schemas": {
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Resurso nerasta"}
                },
                "required": ["error"]
            },
            "MessageResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Operacija sėkmingai atlikta"}
                },
                "required": ["message"]
            },
            "Project": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Verslo centro „Kauno Dokas“ renovacija"},
                    "latitude": {"type": "number", "nullable": True, "example": 54.9027},
                    "longitude": {"type": "number", "nullable": True, "example": 23.8863},
                    "address": {"type": "string", "nullable": True, "example": "Jonavos g. 7, Kaunas"},
                    "is_completed": {"type": "boolean", "example": False}
                }
            },
            "ProjectInput": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "minLength": 2, "maxLength": 200, "example": "Saulės elektrinės montavimas"},
                    "latitude": {"type": "number", "minimum": -90, "maximum": 90, "nullable": True, "example": 54.8985},
                    "longitude": {"type": "number", "minimum": -180, "maximum": 180, "nullable": True, "example": 23.9036},
                    "address": {"type": "string", "maxLength": 500, "nullable": True, "example": "Laisvės al. 50, Kaunas"},
                    "is_completed": {"type": "boolean", "example": False}
                }
            },
            "Task": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "project_id": {"type": "integer", "example": 1},
                    "title": {"type": "string", "example": "Elektros instaliacijos paruošimas"},
                    "name": {"type": "string", "example": "Elektros instaliacijos paruošimas"},
                    "description": {"type": "string", "nullable": True, "example": "Kabelių vedžiojimas 2 aukšte ir paskirstymo dėžutės"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "done"], "example": "in_progress"},
                    "created_at": {"type": "string", "format": "date-time", "example": "2026-10-15T08:30:00"}
                }
            },
            "TaskInput": {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string", "minLength": 2, "maxLength": 200, "example": "Šviestuvų montavimas"},
                    "description": {"type": "string", "maxLength": 500, "nullable": True, "example": "LED panelių montavimas konferencijų salėje"},
                    "status": {"type": "string", "enum": ["todo", "in_progress", "done"], "default": "todo", "example": "todo"}
                }
            },
            "WorkHours": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 3},
                    "project_id": {"type": "integer", "nullable": True, "example": 1},
                    "project_name": {"type": "string", "nullable": True, "example": "Verslo centro „Kauno Dokas“ renovacija"},
                    "task_id": {"type": "integer", "nullable": True, "example": 1},
                    "task_title": {"type": "string", "nullable": True, "example": "Elektros instaliacijos paruošimas"},
                    "date": {"type": "string", "format": "date", "example": "2026-10-15"},
                    "hours": {"type": "number", "example": 8.0},
                    "start_time": {"type": "string", "example": "08:00"},
                    "end_time": {"type": "string", "example": "17:00"},
                    "lunch_break": {"type": "integer", "nullable": True, "example": 60},
                    "notes": {"type": "string", "nullable": True, "example": "Sumontuoti 12 šviestuvų"}
                }
            },
            "WorkHoursInput": {
                "type": "object",
                "required": ["date", "start_time", "end_time"],
                "properties": {
                    "date": {"type": "string", "format": "date", "example": "2026-10-16"},
                    "start_time": {"type": "string", "example": "08:00"},
                    "end_time": {"type": "string", "example": "17:00"},
                    "lunch_break": {"type": "integer", "minimum": 0, "maximum": 480, "nullable": True, "example": 60},
                    "notes": {"type": "string", "maxLength": 255, "nullable": True, "example": "Atlikti kabelių matavimai"}
                }
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "username": {"type": "string", "example": "jonas"},
                    "email": {"type": "string", "nullable": True, "example": "jonas@workerh.lt"},
                    "first_name": {"type": "string", "example": "Jonas"},
                    "last_name": {"type": "string", "example": "Kazlauskas"},
                    "role": {"type": "string", "enum": ["worker", "manager", "admin"], "example": "worker"},
                    "is_active": {"type": "boolean", "example": True}
                }
            },
            "LeaveRequest": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "user_id": {"type": "integer", "example": 3},
                    "type": {"type": "string", "enum": ["vacation", "sick"], "example": "vacation"},
                    "start_date": {"type": "string", "format": "date", "example": "2026-11-02"},
                    "end_date": {"type": "string", "format": "date", "example": "2026-11-06"},
                    "days": {"type": "integer", "example": 5},
                    "notes": {"type": "string", "nullable": True, "example": "Rudens atostogos"},
                    "status": {"type": "string", "enum": ["pending", "approved", "denied"], "example": "pending"},
                    "reviewed_by": {"type": "integer", "nullable": True, "example": 2},
                    "reviewed_at": {"type": "string", "format": "date-time", "nullable": True}
                }
            }
        }
    },
    "security": [
        {"cookieAuth": []},
        {"basicAuth": []}
    ],
    "paths": {
        # ====================================================================
        # 1 LYGMUO: PROJEKTAI (5 metodai)
        # ====================================================================
        "/api/projects": {
            "get": {
                "tags": ["1. Projektai (Project - 1 lygmuo)"],
                "summary": "1. Gauti visų projektų sąrašą",
                "operationId": "getProjects",
                "responses": {
                    "200": {
                        "description": "Projektų sąrašas",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"$ref": "#/components/schemas/Project"}}
                            }
                        }
                    },
                    "401": {"description": "Neprisijungęs naudotojas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "post": {
                "tags": ["1. Projektai (Project - 1 lygmuo)"],
                "summary": "3. Sukurti naują projektą",
                "operationId": "createProject",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProjectInput"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Projektas sėkmingai sukurtas",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Project"}}}
                    },
                    "400": {"description": "Trūksta privalomų laukų arba netinkamas JSON", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "401": {"description": "Neprisijungęs naudotojas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "403": {"description": "Prieiga uždrausta (reikalinga manager arba admin rolė)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "422": {"description": "Validacijos klaida (pvz. per trumpas pavadinimas arba netinkamos koordinatės)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            }
        },
        "/api/projects/{project_id}": {
            "parameters": [
                {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Projekto ID"}
            ],
            "get": {
                "tags": ["1. Projektai (Project - 1 lygmuo)"],
                "summary": "2. Gauti konkretų projektą pagal ID",
                "operationId": "getProjectById",
                "responses": {
                    "200": {
                        "description": "Projekto duomenys",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Project"}}}
                    },
                    "401": {"description": "Neprisijungęs naudotojas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "put": {
                "tags": ["1. Projektai (Project - 1 lygmuo)"],
                "summary": "4. Atnaujinti projektą pagal ID",
                "operationId": "updateProject",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProjectInput"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Projektas atnaujintas",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Project"}}}
                    },
                    "400": {"description": "Trūksta atnaujinamų duomenų", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "422": {"description": "Validacijos klaida", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "delete": {
                "tags": ["1. Projektai (Project - 1 lygmuo)"],
                "summary": "5. Ištrinti projektą pagal ID",
                "operationId": "deleteProject",
                "responses": {
                    "200": {
                        "description": "Projektas ištrintas",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}
                    },
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            }
        },
        # ====================================================================
        # 2 LYGMUO: UŽDUOTYS PROJEKTE (5 metodai)
        # ====================================================================
        "/api/projects/{project_id}/tasks": {
            "parameters": [
                {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Projekto ID"}
            ],
            "get": {
                "tags": ["2. Užduotys (Task - 2 lygmuo)"],
                "summary": "6. Gauti visų konkretaus projekto užduočių sąrašą",
                "operationId": "getProjectTasks",
                "responses": {
                    "200": {
                        "description": "Projekto užduočių sąrašas",
                        "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Task"}}}}
                    },
                    "404": {"description": "Projektas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "post": {
                "tags": ["2. Užduotys (Task - 2 lygmuo)"],
                "summary": "8. Sukurti naują užduotį konkrečiame projekte",
                "operationId": "createProjectTask",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TaskInput"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Užduotis sėkmingai sukurta",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}
                    },
                    "400": {"description": "Trūksta privalomų laukų (title)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "422": {"description": "Validacijos klaida (pvz. netinkama būsena arba per trumpas pavadinimas)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            }
        },
        "/api/projects/{project_id}/tasks/{task_id}": {
            "parameters": [
                {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Projekto ID"},
                {"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Užduoties ID"}
            ],
            "get": {
                "tags": ["2. Užduotys (Task - 2 lygmuo)"],
                "summary": "7. Gauti konkrečią projekto užduotį pagal ID",
                "operationId": "getProjectTaskById",
                "responses": {
                    "200": {
                        "description": "Užduoties informacija",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}
                    },
                    "404": {"description": "Projektas arba užduotis nerasta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "put": {
                "tags": ["2. Užduotys (Task - 2 lygmuo)"],
                "summary": "9. Atnaujinti konkrečią projekto užduotį",
                "operationId": "updateProjectTask",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TaskInput"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Užduotis atnaujinta",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Task"}}}
                    },
                    "400": {"description": "Trūksta atnaujinamų duomenų", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas arba užduotis nerasta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "422": {"description": "Validacijos klaida", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "delete": {
                "tags": ["2. Užduotys (Task - 2 lygmuo)"],
                "summary": "10. Ištrinti konkrečią projekto užduotį",
                "operationId": "deleteProjectTask",
                "responses": {
                    "200": {
                        "description": "Užduotis ištrinta",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}
                    },
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas arba užduotis nerasta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            }
        },
        # ====================================================================
        # 3 LYGMUO: DARBO LAIKO ĮRAŠAI UŽDUOTYJE (5 metodai)
        # ====================================================================
        "/api/projects/{project_id}/tasks/{task_id}/hours": {
            "parameters": [
                {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Projekto ID"},
                {"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Užduoties ID"}
            ],
            "get": {
                "tags": ["3. Darbo laikas (WorkHours - 3 lygmuo)"],
                "summary": "11. Gauti visus konkrečios projekto užduoties darbo laiko įrašus",
                "operationId": "getTaskHours",
                "responses": {
                    "200": {
                        "description": "Darbo laiko įrašų sąrašas",
                        "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/WorkHours"}}}}
                    },
                    "404": {"description": "Projektas arba užduotis nerasta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "post": {
                "tags": ["3. Darbo laikas (WorkHours - 3 lygmuo)"],
                "summary": "13. Sukurti naują darbo laiko įrašą konkrečiai projekto užduočiai",
                "operationId": "createTaskHours",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WorkHoursInput"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Darbo laiko įrašas sukurtas",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WorkHours"}}}
                    },
                    "400": {"description": "Trūksta privalomų laukų (date, start_time, end_time)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas arba užduotis nerasta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "422": {"description": "Validacijos klaida (pvz. neigiamas darbo laikas arba persidengiantys įrašai)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            }
        },
        "/api/projects/{project_id}/tasks/{task_id}/hours/{entry_id}": {
            "parameters": [
                {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Projekto ID"},
                {"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Užduoties ID"},
                {"name": "entry_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "Darbo laiko įrašo ID"}
            ],
            "get": {
                "tags": ["3. Darbo laikas (WorkHours - 3 lygmuo)"],
                "summary": "12. Gauti konkretų projekto užduoties darbo laiko įrašą pagal ID",
                "operationId": "getTaskHoursById",
                "responses": {
                    "200": {
                        "description": "Darbo laiko įrašo duomenys",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WorkHours"}}}
                    },
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas, užduotis arba darbo laiko įrašas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "put": {
                "tags": ["3. Darbo laikas (WorkHours - 3 lygmuo)"],
                "summary": "14. Atnaujinti konkretų projekto užduoties darbo laiko įrašą",
                "operationId": "updateTaskHours",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WorkHoursInput"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Darbo laiko įrašas atnaujintas",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WorkHours"}}}
                    },
                    "400": {"description": "Trūksta privalomų laukų", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas, užduotis arba darbo laiko įrašas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "422": {"description": "Validacijos klaida", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            },
            "delete": {
                "tags": ["3. Darbo laikas (WorkHours - 3 lygmuo)"],
                "summary": "15. Ištrinti konkretų projekto užduoties darbo laiko įrašą",
                "operationId": "deleteTaskHours",
                "responses": {
                    "200": {
                        "description": "Darbo laiko įrašas ištrintas",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}
                    },
                    "403": {"description": "Prieiga uždrausta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    "404": {"description": "Projektas, užduotis arba darbo laiko įrašas nerastas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                }
            }
        },
        # ====================================================================
        # KITI SISTEMOS API METODAI (Auth, Leave, Users, Invites, Hours)
        # ====================================================================
        "/api/auth/login": {
            "post": {
                "tags": ["Autentifikacija (Auth)"],
                "summary": "Prisijungti prie sistemos",
                "security": [],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "password"],
                                "properties": {
                                    "username": {"type": "string", "example": "admin"},
                                    "password": {"type": "string", "example": "admin123"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Sėkmingai prisijungta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}},
                    "400": {"description": "Trūksta laukų"},
                    "401": {"description": "Neteisingi prisijungimo duomenys"},
                    "403": {"description": "Paskyra išjungta"}
                }
            }
        },
        "/api/auth/logout": {
            "post": {
                "tags": ["Autentifikacija (Auth)"],
                "summary": "Atsijungti nuo sistemos",
                "responses": {
                    "200": {"description": "Atsijungta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}}
                }
            }
        },
        "/api/auth/me": {
            "get": {
                "tags": ["Autentifikacija (Auth)"],
                "summary": "Gauti prisijungusio naudotojo profilį",
                "responses": {
                    "200": {"description": "Naudotojo informacija", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}},
                    "401": {"description": "Neprisijungęs"}
                }
            }
        },
        "/api/hours": {
            "get": {
                "tags": ["Darbo valandos (Plokšti maršrutai)"],
                "summary": "Gauti darbo valandų sąrašą (su filtravimu)",
                "responses": {
                    "200": {"description": "Darbo valandų sąrašas", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/WorkHours"}}}}}
                }
            },
            "post": {
                "tags": ["Darbo valandos (Plokšti maršrutai)"],
                "summary": "Pridėti darbo valandų įrašą",
                "responses": {
                    "201": {"description": "Sukurta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/WorkHours"}}}}
                }
            }
        },
        "/api/leave": {
            "get": {
                "tags": ["Atostogos ir nedarbingumas (Leave)"],
                "summary": "Gauti atostogų ir nedarbingumo prašymų sąrašą",
                "responses": {
                    "200": {"description": "Prašymų sąrašas", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/LeaveRequest"}}}}}
                }
            },
            "post": {
                "tags": ["Atostogos ir nedarbingumas (Leave)"],
                "summary": "Pateikti atostogų arba nedarbingumo prašymą",
                "responses": {
                    "201": {"description": "Prašymas sukurtas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LeaveRequest"}}}}
                }
            }
        },
        "/api/users": {
            "get": {
                "tags": ["Naudotojai ir pakvietimai (Users & Invites)"],
                "summary": "Gauti visų naudotojų sąrašą",
                "responses": {
                    "200": {"description": "Naudotojų sąrašas", "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/User"}}}}}
                }
            }
        },
        "/api/users/{user_id}/dismiss": {
            "parameters": [
                {"name": "user_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "patch": {
                "tags": ["Naudotojai ir pakvietimai (Users & Invites)"],
                "summary": "Blokuoti (atleisti) naudotojo paskyrą",
                "responses": {
                    "200": {"description": "Paskyra išjungta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}},
                    "404": {"description": "Naudotojas nerastas"}
                }
            }
        },
        "/api/users/{user_id}/reactivate": {
            "parameters": [
                {"name": "user_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "patch": {
                "tags": ["Naudotojai ir pakvietimai (Users & Invites)"],
                "summary": "Aktyvuoti naudotojo paskyrą",
                "responses": {
                    "200": {"description": "Paskyra aktyvuota", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}},
                    "404": {"description": "Naudotojas nerastas"}
                }
            }
        },
        "/api/invites": {
            "get": {
                "tags": ["Naudotojai ir pakvietimai (Users & Invites)"],
                "summary": "Gauti išsiųstų pakvietimų sąrašą",
                "responses": {
                    "200": {"description": "Pakvietimų sąrašas"}
                }
            },
            "post": {
                "tags": ["Naudotojai ir pakvietimai (Users & Invites)"],
                "summary": "Sukurti ir išsiųsti pakvietimą el. paštu",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email"],
                                "properties": {
                                    "email": {"type": "string", "example": "naujas@workerh.lt"},
                                    "role": {"type": "string", "enum": ["worker", "manager", "admin"], "default": "worker"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Pakvietimas sukurtas"}
                }
            }
        },
        "/api/invites/{invite_id}": {
            "parameters": [
                {"name": "invite_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "delete": {
                "tags": ["Naudotojai ir pakvietimai (Users & Invites)"],
                "summary": "Atšaukti pakvietimą",
                "responses": {
                    "200": {"description": "Pakvietimas atšauktas"},
                    "404": {"description": "Pakvietimas nerastas"}
                }
            }
        },
        "/api/leave/{req_id}": {
            "parameters": [
                {"name": "req_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "get": {
                "tags": ["Atostogos ir nedarbingumas (Leave)"],
                "summary": "Gauti konkretų atostogų / nedarbingumo prašymą",
                "responses": {
                    "200": {"description": "Prašymo duomenys", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LeaveRequest"}}}},
                    "404": {"description": "Prašymas nerastas"}
                }
            },
            "delete": {
                "tags": ["Atostogos ir nedarbingumas (Leave)"],
                "summary": "Atšaukti atostogų / nedarbingumo prašymą",
                "responses": {
                    "200": {"description": "Prašymas atšauktas"},
                    "404": {"description": "Prašymas nerastas"}
                }
            }
        },
        "/api/leave/{req_id}/review": {
            "parameters": [
                {"name": "req_id", "in": "path", "required": True, "schema": {"type": "integer"}}
            ],
            "patch": {
                "tags": ["Atostogos ir nedarbingumas (Leave)"],
                "summary": "Patvirtinti arba atmesti atostogų prašymą",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["status"],
                                "properties": {
                                    "status": {"type": "string", "enum": ["approved", "denied"], "example": "approved"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Prašymo būsena atnaujinta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LeaveRequest"}}}},
                    "404": {"description": "Prašymas nerastas"}
                }
            }
        }
    }
}

