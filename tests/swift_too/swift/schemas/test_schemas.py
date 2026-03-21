from datetime import datetime, timedelta

from swifttools.swift_too.swift.schemas import SwiftObservationSchema


class TestSwiftObservationSchema:
    def test_settle_field_is_declared(self):
        schema = SwiftObservationSchema(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
        )

        assert schema.settle == datetime(2023, 1, 1, 12, 1, 0)

    def test_time_properties_are_none_safe(self):
        schema = SwiftObservationSchema(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
        )

        assert schema.exposure is None
        assert schema.slewtime is None

    def test_table_uses_none_when_deltas_unavailable(self):
        schema = SwiftObservationSchema(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
            target_name="Test Target",
            obs_id="00012345001",
        )

        _, data = schema._table
        assert data[0][4] is None
        assert data[0][5] is None

    def test_time_properties_when_complete(self):
        schema = SwiftObservationSchema(
            begin=datetime(2023, 1, 1, 12, 0, 0),
            settle=datetime(2023, 1, 1, 12, 1, 0),
            end=datetime(2023, 1, 1, 12, 10, 0),
        )

        assert schema.exposure == timedelta(minutes=9)
        assert schema.slewtime == timedelta(minutes=1)
