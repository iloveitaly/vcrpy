import itertools

import pytest

from vcr import matchers
from vcr import request

# the dict contains requests with corresponding to its key difference
# with 'base' request.
REQUESTS = {
    'base': request.Request('GET', 'http://host.com/p?a=b', '', {}),
    'method': request.Request('POST', 'http://host.com/p?a=b', '', {}),
    'scheme': request.Request('GET', 'https://host.com:80/p?a=b', '', {}),
    'host': request.Request('GET', 'http://another-host.com/p?a=b', '', {}),
    'port': request.Request('GET', 'http://host.com:90/p?a=b', '', {}),
    'path': request.Request('GET', 'http://host.com/x?a=b', '', {}),
    'query': request.Request('GET', 'http://host.com/p?c=d', '', {}),
}


def assert_matcher(matcher_name):
    matcher = getattr(matchers, matcher_name)
    for k1, k2 in itertools.permutations(REQUESTS, 2):
        matched = matcher(REQUESTS[k1], REQUESTS[k2])
        if matcher_name in {k1, k2}:
            assert not matched
        else:
            assert matched


def test_uri_matcher():
    for k1, k2 in itertools.permutations(REQUESTS, 2):
        matched = matchers.uri(REQUESTS[k1], REQUESTS[k2])
        if {k1, k2} != {'base', 'method'}:
            assert not matched
        else:
            assert matched


req1_body = (b"<?xml version='1.0'?><methodCall><methodName>test</methodName>"
             b"<params><param><value><array><data><value><struct>"
             b"<member><name>a</name><value><string>1</string></value></member>"
             b"<member><name>b</name><value><string>2</string></value></member>"
             b"</struct></value></data></array></value></param></params></methodCall>")
req2_body = (b"<?xml version='1.0'?><methodCall><methodName>test</methodName>"
             b"<params><param><value><array><data><value><struct>"
             b"<member><name>b</name><value><string>2</string></value></member>"
             b"<member><name>a</name><value><string>1</string></value></member>"
             b"</struct></value></data></array></value></param></params></methodCall>")


@pytest.mark.parametrize("r1, r2", [
    (
        request.Request('POST', 'http://host.com/', '123', {}),
        request.Request('POST', 'http://another-host.com/',
                        '123', {'Some-Header': 'value'})
    ),
    (
        request.Request('POST', 'http://host.com/', 'a=1&b=2',
                        {'Content-Type': 'application/x-www-form-urlencoded'}),
        request.Request('POST', 'http://host.com/', 'b=2&a=1',
                        {'Content-Type': 'application/x-www-form-urlencoded'})
    ),
    (
        request.Request('POST', 'http://host.com/', '123', {}),
        request.Request('POST', 'http://another-host.com/', '123', {'Some-Header': 'value'})
    ),
    (
        request.Request(
            'POST', 'http://host.com/', 'a=1&b=2',
            {'Content-Type': 'application/x-www-form-urlencoded'}
        ),
        request.Request(
            'POST', 'http://host.com/', 'b=2&a=1',
            {'Content-Type': 'application/x-www-form-urlencoded'}
        )
    ),
    (
        request.Request(
            'POST', 'http://host.com/', '{"a": 1, "b": 2}',
            {'Content-Type': 'application/json'}
        ),
        request.Request(
            'POST', 'http://host.com/', '{"b": 2, "a": 1}',
            {'content-type': 'application/json'}
        )
    ),
    (
        request.Request(
            'POST', 'http://host.com/', req1_body,
            {'User-Agent': 'xmlrpclib', 'Content-Type': 'text/xml'}
        ),
        request.Request(
            'POST', 'http://host.com/', req2_body,
            {'user-agent': 'somexmlrpc', 'content-type': 'text/xml'}
        )
    ),
    (
        request.Request(
            'POST', 'http://host.com/',
            '{"a": 1, "b": 2}', {'Content-Type': 'application/json'}
        ),
        request.Request(
            'POST', 'http://host.com/',
            '{"b": 2, "a": 1}', {'content-type': 'application/json'}
        )
    )
])
def test_body_matcher_does_match(r1, r2):
    assert matchers.body(r1, r2)


@pytest.mark.parametrize("r1, r2", [
    (
        request.Request('POST', 'http://host.com/', '{"a": 1, "b": 2}', {}),
        request.Request('POST', 'http://host.com/', '{"b": 2, "a": 1}', {}),
    ),
    (
        request.Request(
            'POST', 'http://host.com/',
            '{"a": 1, "b": 3}', {'Content-Type': 'application/json'}
        ),
        request.Request(
            'POST', 'http://host.com/',
            '{"b": 2, "a": 1}', {'content-type': 'application/json'}
        )
    ),
    (
        request.Request(
            'POST', 'http://host.com/', req1_body, {'Content-Type': 'text/xml'}
        ),
        request.Request(
            'POST', 'http://host.com/', req2_body, {'content-type': 'text/xml'}
        )
    )
])
def test_body_match_does_not_match(r1, r2):
    assert not matchers.body(r1, r2)


def test_query_matcher():
    req1 = request.Request('GET', 'http://host.com/?a=b&c=d', '', {})
    req2 = request.Request('GET', 'http://host.com/?c=d&a=b', '', {})
    assert matchers.query(req1, req2)

def test_evaluate_matcher_does_match():
    def bool_matcher(r1, r2):
        return True

    def assertion_matcher(r1, r2):
        assert 1 == 1

    r1, r2 = None, None
    for matcher in [bool_matcher, assertion_matcher]:
        match, assertion_msg = matchers._evaluate_matcher(matcher, r1, r2)
        assert match is True
        assert assertion_msg is None


def test_evaluate_matcher_does_not_match():
    def bool_matcher(r1, r2):
        return False

    def assertion_matcher(r1, r2):
        # This is like the "assert" statement preventing pytest to recompile it
        raise AssertionError()

    r1, r2 = None, None
    for matcher in [bool_matcher, assertion_matcher]:
        match, assertion_msg = matchers._evaluate_matcher(matcher, r1, r2)
        assert match is False
        assert not assertion_msg


def test_evaluate_matcher_does_not_match_with_assert_message():
    def assertion_matcher(r1, r2):
        # This is like the "assert" statement preventing pytest to recompile it
        raise AssertionError("Failing matcher")

    r1, r2 = None, None
    match, assertion_msg = matchers._evaluate_matcher(assertion_matcher, r1, r2)
    assert match is False
    assert assertion_msg == "Failing matcher"


def test_get_assertion_message():
    assert matchers.get_assertion_message(None) == ""
    assert matchers.get_assertion_message("") == ""


def test_get_assertion_message_with_details():
    assertion_msg = "q1=1 != q2=1"
    expected = (
        "--------------- DETAILS ---------------\n"
        "{}\n"
        "----------------------------------------\n".format(assertion_msg)
    )
    assert matchers.get_assertion_message(assertion_msg) == expected
