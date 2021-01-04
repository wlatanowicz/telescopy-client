from core.autofocus import Autofocus
from .helpers import ConnectorMock


def test_autofocus():
    conn = ConnectorMock()

    af = Autofocus(conn)
    af.autofocus(3, 380, 480, 10, 3)

    assert conn.focus == 432
