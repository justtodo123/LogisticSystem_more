import redis


def test_redis_service_responds_to_ping(p1_redis_url: str):
    client = redis.Redis.from_url(p1_redis_url)
    try:
        assert client.ping() is True
    finally:
        client.close()
