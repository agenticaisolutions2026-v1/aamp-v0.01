from backend.services.college_discovery_service import CollegeDiscoveryService


def run_test():
    service = CollegeDiscoveryService()

    result = service.discover_colleges(
        state="Andhra Pradesh",
        category="engineering colleges",
        target_count=10
    )

    print("=== College Discovery Result ===")
    print(result)


if __name__ == "__main__":
    run_test()