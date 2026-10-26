from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.test import APIRequestFactory

from apps.common.exceptions import DomainError


class ExampleError(DomainError):
    status_code = 409
    code = "example"
    default_message = "Example message."


class ExampleSerializer(serializers.Serializer):
    name = serializers.CharField()


def call(view_body):
    @api_view(["POST"])
    def view(request):
        view_body(request)

    return view(APIRequestFactory().post("/", {}, format="json"))


def test_domain_error_uses_its_status_code_and_message():
    def body(request):
        raise ExampleError(details={"hint": "x"})

    response = call(body)

    assert response.status_code == 409
    assert response.data == {
        "error": {"code": "example", "message": "Example message.", "details": {"hint": "x"}}
    }


def test_validation_error_lists_field_errors_in_details():
    def body(request):
        ExampleSerializer(data=request.data).is_valid(raise_exception=True)

    response = call(body)

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid"
    assert "name" in response.data["error"]["details"]


def test_http404_is_formatted_as_not_found():
    def body(request):
        raise Http404

    response = call(body)

    assert response.status_code == 404
    assert response.data["error"]["code"] == "not_found"
