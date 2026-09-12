from flask import Blueprint, jsonify
openapi_bp = Blueprint("openapi", __name__)
@openapi_bp.route("/api/v1/openapi.json")
def openapi_spec():
    spec={
        "openapi":"3.0.0",
        "info":{"title":"F1 Predictor 2026 API","version":"1.0.0","description":"Flask REST API with versioned /api/v1 contracts. Preserves prediction engine parity."},
        "servers":[{"url":"/api/v1"}],
        "paths":{
            "/races":{"get":{"summary":"List races","responses":{"200":{"description":"calendar"}}}},
            "/predictions":{"post":{"summary":"Generate prediction","responses":{"200":{"description":"prediction"}}}},
            "/standings/drivers":{"get":{"summary":"Driver standings"}},
            "/standings/constructors":{"get":{"summary":"Constructor standings"}},
            "/h2h/drivers":{"get":{"summary":"List drivers"}},
            "/h2h/compare":{"post":{"summary":"H2H compare"}},
            "/constructors/teams":{"get":{"summary":"Teams"}},
            "/constructors/power-rankings":{"get":{"summary":"Power rankings"}},
            "/analytics/accuracy":{"get":{"summary":"Accuracy"}},
            "/analytics/feature-weights":{"get":{"summary":"Feature weights"},"post":{"summary":"Update weights"}},
            "/analytics/targets":{"get":{"summary":"Targets"}},
            "/reports/export":{"post":{"summary":"Export"}},
            "/ai/chat":{"post":{"summary":"AI chat"}},
            "/health":{"get":{"summary":"Health"}},
        }
    }
    return jsonify(spec)
@openapi_bp.route("/api/docs")
def docs():
    return jsonify({"message":"OpenAPI available at /api/v1/openapi.json","swagger_ui":"/api/docs not bundled — use openapi.json"})
