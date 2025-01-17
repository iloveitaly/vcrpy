from unittest import mock

from vcr import mode
from vcr.stubs import VCRHTTPSConnection
from vcr.cassette import Cassette


class TestVCRConnection:
    def test_setting_of_attributes_get_propagated_to_real_connection(self):
        vcr_connection = VCRHTTPSConnection("www.examplehost.com")
        vcr_connection.ssl_version = "example_ssl_version"
        assert vcr_connection.real_connection.ssl_version == "example_ssl_version"

    @mock.patch("vcr.cassette.Cassette.can_play_response_for", return_value=False)
    def testing_connect(*args):
        vcr_connection = VCRHTTPSConnection("www.google.com")
        vcr_connection.cassette = Cassette("test", record_mode=mode.ALL)
        vcr_connection.real_connection.connect()
        assert vcr_connection.real_connection.sock is not None
