from sqlalchemy import text
import json

from backend.tools.college_discovery.tavily_search_client import (
    TavilySearchClient
)
from backend.tools.college_discovery.tavily_source_filter import TavilySourceFilter
from backend.tools.college_discovery.tavily_page_reader import (
    TavilyPageReader
)

from backend.tools.college_discovery.tavily_college_extractor import (
    CollegeExtractor
)
from backend.tools.college_discovery.tavily_college_normalizer import (
    TavilyCollegeNormalizer
)

from backend.tools.college_discovery.deduplicator import Deduplicator
from backend.tools.college_discovery.tavily_content_college_extractor import (
    TavilyContentCollegeExtractor
)

from backend.tools.college_discovery.tavily_admissionteam_college_extractor import (
    AdmissionTeamCollegeExtractor
)

from backend.tools.college_discovery.tavily_careers360_college_extractor import (
    Careers360CollegeExtractor
)

from backend.tools.college_discovery.tavily_wikipedia_college_extractor import (
    WikipediaCollegeExtractor
)
from backend.tools.college_discovery.tavily_college_website_finder import (
    TavilyCollegeWebsiteFinder
)

from backend.tools.college_discovery.tavily_college_website_reader import (
    TavilyCollegeWebsiteReader
)

from backend.tools.college_discovery.tavily_college_contact_page_finder import (
    TavilyCollegeContactPageFinder
)

from backend.tools.college_discovery.tavily_college_contact_extractor import (
    TavilyCollegeContactExtractor
)

from backend.tools.college_discovery.tavily_contact_search import (
    TavilyContactSearch
)

from backend.tools.college_discovery.tavily_college_web_enricher import (
    TavilyCollegeWebEnricher
)

import requests
from bs4 import BeautifulSoup


def run_test():

    client = TavilySearchClient()
    source_filter = TavilySourceFilter()

    raw = client.search(
        "engineering colleges in Andhra Pradesh",
        max_results=10
    )

    sources = source_filter.filter(
        raw.get("results", [])
    )

    print("=== FILTERED SOURCES ===")
    print("Number of sources:", len(sources))

    for index, source in enumerate(sources, start=1):
        print(f"\n--- Source {index} ---")
        print("Title:", source["title"])
        print("URL:", source["url"])
        print("Score:", source["score"])

def test_tavily_multiple_sources():

    search_client = TavilySearchClient()
    source_filter = TavilySourceFilter()
    reader = TavilyPageReader()
    extractor = CollegeExtractor()
    normalizer = TavilyCollegeNormalizer()
    deduplicator = Deduplicator()

    # 1. Search Tavily
    raw_results = search_client.search(
        "engineering colleges in Andhra Pradesh",
        max_results=10
    )

    # 2. Filter useful sources
    sources = source_filter.filter(
        raw_results.get("results", [])
    )

    all_colleges = []

    # 3. Process every source
    print("\n=== BLOCKED SOURCE TAVILY CONTENT ===")

    for source in sources:

        url = source.get("url", "")

        if "shiksha.com" in url:
            print("Title:", source.get("title"))
            print("URL:", url)
            print("Content:")
            print(source.get("content", ""))
            break

        # Extract college candidates
        extracted = extractor.extract(text)

        print("Extracted:", len(extracted))

        # Normalize
        normalized = normalizer.normalize(
            extracted,
            state="Andhra Pradesh",
            source_url=url
        )

        if "careers360.com" in url:
            print("\n=== CAREERS360 FIRST 20 ===")

            for college in normalized[:20]:
                print(college)

            print("\n=== CAREERS360 LAST 20 ===")

            for college in normalized[-20:]:
                print(college)

        print("Normalized:", len(normalized))

        all_colleges.extend(normalized)

    # 4. Deduplicate across ALL sources
    unique_colleges = deduplicator.deduplicate(
        all_colleges
    )

    print("\n================================")
    print("=== MULTI-SOURCE RESULT ===")
    print("Sources processed:", len(sources))
    print("Total before deduplication:", len(all_colleges))
    print("Total after deduplication:", len(unique_colleges))

def test_admissionteam_duplicates():

    reader = TavilyPageReader()
    extractor = CollegeExtractor()
    admissionteam_extractor = AdmissionTeamCollegeExtractor()
    normalizer = TavilyCollegeNormalizer()
    deduplicator = Deduplicator()

    # TopCollegeAdmission
    topcollege_url = (
        "https://topcollegeadmission.in/"
        "index.php/2025/03/24/"
        "list-of-engineering-colleges-in-andhra-pradesh"
    )

    text = reader.read(topcollege_url)

    top_extracted = extractor.extract(text)

    top_colleges = normalizer.normalize(
        top_extracted,
        state="Andhra Pradesh",
        source_url=topcollege_url
    )

    print("\n=== TOPCOLLEGE DUPLICATE KEYS ===")

    top_name_map = {}

    for college in top_colleges:

        key = deduplicator._normalize_name(
            college.get("name", "")
        )

        if key in top_name_map:

            print("\nDUPLICATE KEY:", key)

            print("FIRST:")
            print(top_name_map[key])

            print("SECOND:")
            print(college)

        else:
            top_name_map[key] = college

    # AdmissionTeam
    admissionteam_url = (
        "https://www.admissionteam.com/"
        "engineering-college-available-in-andhra-pradesh"
    )

    text = reader.read(admissionteam_url)

    admissionteam_extracted = admissionteam_extractor.extract(text)

    admissionteam_colleges = normalizer.normalize(
        admissionteam_extracted,
        state="Andhra Pradesh",
        source_url=admissionteam_url
    )

   # Combine
    all_colleges = top_colleges + admissionteam_colleges

    # 👇 ADD THE NEW DIAGNOSTIC CODE HERE

    print("\n=== NORMALIZED ADMISSIONTEAM NAMES ===")

    for college in admissionteam_colleges:
        print(
            college["name"],
            "→",
            deduplicator._normalize_name(college["name"])
        )

    print("\n=== NORMALIZED TOPCOLLEGE NAMES MATCHING ADMISSIONTEAM ===")

    top_name_map = {
        deduplicator._normalize_name(college["name"]): college["name"]
        for college in top_colleges
    }

    for college in admissionteam_colleges:

        normalized_name = deduplicator._normalize_name(
            college["name"]
        )

        if normalized_name in top_name_map:
            print(
                "DUPLICATE:",
                college["name"],
                "↔",
                top_name_map[normalized_name]
            )

    # Deduplicate AFTER the diagnostic loop
    unique_colleges = deduplicator.deduplicate(
        all_colleges
    )

    print("\n=== FINAL DEDUPLICATION ===")
    print("Before:", len(all_colleges))
    print("After:", len(unique_colleges))

def test_two_source_pipeline():

    reader = TavilyPageReader()
    extractor = CollegeExtractor()
    admissionteam_extractor = AdmissionTeamCollegeExtractor()
    normalizer = TavilyCollegeNormalizer()
    deduplicator = Deduplicator()

    all_colleges = []

    # ---------------------------------
    # Source 1: TopCollegeAdmission
    # ---------------------------------

    topcollege_url = (
        "https://topcollegeadmission.in/"
        "index.php/2025/03/24/"
        "list-of-engineering-colleges-in-andhra-pradesh"
    )

    print("\n================================")
    print("SOURCE: TopCollegeAdmission")

    text = reader.read(topcollege_url)

    if text:

        extracted = extractor.extract(text)

        normalized = normalizer.normalize(
            extracted,
            state="Andhra Pradesh",
            source_url=topcollege_url
        )

        print("Extracted:", len(extracted))
        print("Normalized:", len(normalized))

        all_colleges.extend(normalized)

    # ---------------------------------
    # Source 2: AdmissionTeam
    # ---------------------------------

    admissionteam_url = (
        "https://www.admissionteam.com/"
        "engineering-college-available-in-andhra-pradesh"
    )

    print("\n================================")
    print("SOURCE: AdmissionTeam")

    text = reader.read(admissionteam_url)

    if text:

        extracted = admissionteam_extractor.extract(text)

        normalized = normalizer.normalize(
            extracted,
            state="Andhra Pradesh",
            source_url=admissionteam_url
        )

        print("Extracted:", len(extracted))
        print("Normalized:", len(normalized))

        all_colleges.extend(normalized)

    # ---------------------------------
    # Final deduplication
    # ---------------------------------

    print("\n================================")
    print("=== COMBINED PIPELINE ===")

    print(
        "Total before deduplication:",
        len(all_colleges)
    )

    unique_colleges = deduplicator.deduplicate(
        all_colleges
    )

    print(
        "Total after deduplication:",
        len(unique_colleges)
    )

    print(
        "Duplicates removed:",
        len(all_colleges) - len(unique_colleges)
    )

def test_careers360_normalizer():

    reader = TavilyPageReader()
    extractor = Careers360CollegeExtractor()
    normalizer = TavilyCollegeNormalizer()

    url = (
        "https://engineering.careers360.com/"
        "colleges/ranking/top-engineering-colleges-in-andhra-pradesh"
    )

    text = reader.read(url)

    colleges = extractor.extract(text)

    normalized = normalizer.normalize(
        colleges,
        state="Andhra Pradesh",
        source_url=url
    )

    print("\n=== CAREERS360 NORMALIZER RESULT ===")
    print("Number of colleges:", len(normalized))

    for college in normalized:
        print(college)


# ----------------------------------------
# Three-source combination test:
# ----------------------------------------
def test_three_source_pipeline():

    reader = TavilyPageReader()
    topcollege_extractor = CollegeExtractor()
    admissionteam_extractor = AdmissionTeamCollegeExtractor()
    careers360_extractor = Careers360CollegeExtractor()
    normalizer = TavilyCollegeNormalizer()
    deduplicator = Deduplicator()

    all_colleges = []

    # ---------------------------------
    # 1. TopCollegeAdmission
    # ---------------------------------

    topcollege_url = (
        "https://topcollegeadmission.in/"
        "index.php/2025/03/24/"
        "list-of-engineering-colleges-in-andhra-pradesh"
    )

    print("\n================================")
    print("SOURCE: TopCollegeAdmission")

    text = reader.read(topcollege_url)

    if text:
        extracted = topcollege_extractor.extract(text)

        normalized = normalizer.normalize(
            extracted,
            state="Andhra Pradesh",
            source_url=topcollege_url
        )

        print("Extracted:", len(extracted))
        print("Normalized:", len(normalized))

        all_colleges.extend(normalized)

    # ---------------------------------
    # 2. AdmissionTeam
    # ---------------------------------

    admissionteam_url = (
        "https://www.admissionteam.com/"
        "engineering-college-available-in-andhra-pradesh"
    )

    print("\n================================")
    print("SOURCE: AdmissionTeam")

    text = reader.read(admissionteam_url)

    if text:
        extracted = admissionteam_extractor.extract(text)

        normalized = normalizer.normalize(
            extracted,
            state="Andhra Pradesh",
            source_url=admissionteam_url
        )

        print("Extracted:", len(extracted))
        print("Normalized:", len(normalized))

        all_colleges.extend(normalized)

    # ---------------------------------
    # 3. Careers360
    # ---------------------------------

    careers360_url = (
        "https://engineering.careers360.com/"
        "colleges/ranking/top-engineering-colleges-in-andhra-pradesh"
    )

    print("\n================================")
    print("SOURCE: Careers360")

    text = reader.read(careers360_url)

    if text:
        extracted = careers360_extractor.extract(text)

        normalized = normalizer.normalize(
            extracted,
            state="Andhra Pradesh",
            source_url=careers360_url
        )

        print("Extracted:", len(extracted))
        print("Normalized:", len(normalized))

        all_colleges.extend(normalized)

    # ---------------------------------
    # Final deduplication
    # ---------------------------------

    print("\n================================")
    print("=== THREE-SOURCE RESULT ===")

    print(
        "Total before deduplication:",
        len(all_colleges)
    )

    unique_colleges = deduplicator.deduplicate(
        all_colleges
    )

    print(
        "Total after deduplication:",
        len(unique_colleges)
    )

    print(
        "Duplicates removed:",
        len(all_colleges) - len(unique_colleges)
    )

    return unique_colleges


# ---------------------------------------------------------
def test_college_web_enricher_batch(colleges):

    enricher = TavilyCollegeWebEnricher()

    enriched_colleges = []
    missing_contact_colleges = []

    total = len(colleges)

    print("\n=== BATCH COLLEGE WEB ENRICHMENT ===")
    print("Total colleges:", total)

    for index, college in enumerate(colleges, start=1):

        name = college.get("name", "")

        print(
            f"[{index}/{total}] {name}",
            end=" ... ",
            flush=True
        )

        try:

            result = enricher.enrich(
                college_name=name,
                state=college.get("state", ""),
                city=college.get("city", ""),
                source_url=college.get("source_url", "")
            )

            enriched_colleges.append(result)

            has_contact = any([
                result.get("address"),
                result.get("phone"),
                result.get("email"),
            ])

            if has_contact:
                print("✓")
            else:
                missing_contact_colleges.append(result)
                print("—")

        except Exception as e:

            print("ERROR:", e)

            missing_contact_colleges.append({
                "name": name,
                "website": college.get("website", ""),
                "state": college.get("state", ""),
                "city": college.get("city", ""),
                "address": "",
                "phone": None,
                "email": None,
                "source_url": college.get("source_url", ""),
                "error": str(e),
            })

    # Save all results
    with open(
        "enriched_colleges.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            enriched_colleges,
            f,
            indent=2,
            ensure_ascii=False
        )

    # Save missing-contact results
    with open(
        "missing_contact_colleges.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            missing_contact_colleges,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n========================================")
    print("ENRICHMENT SUMMARY")
    print("========================================")

    print("Total colleges:", total)

    print(
        "With contact data:",
        total - len(missing_contact_colleges)
    )

    print(
        "Missing contact data:",
        len(missing_contact_colleges)
    )

    print("========================================")

if __name__ == "__main__":

    colleges_402 = test_three_source_pipeline()

    test_college_web_enricher_batch(
        colleges_402
    )