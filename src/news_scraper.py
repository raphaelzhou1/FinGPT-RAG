# https://www.bloomberg.com//search?query=Companies,%20Actelion,%20shares,%20hit,%20record,%20on,%20shares,%20Shire,%20takeover,%20talk&sort=relevance:asc&startTime=2015-04-01T01:01:01.001Z&&page=5

import blpapi

def scrape_bloomberg(subject, page_number, session):
    service = session.getService("//blp/apiflds")
    request = service.createRequest("HistoricalDataRequest")

    request.getElement("securities").appendValue(subject)
    request.getElement("fields").appendValue("URL")
    request.set("sort","relevance:asc")
    request.set("endDate", "2015-08-01")

    session.sendRequest(request)

    links = []
    while True:
        event = session.nextEvent(500)
        if event.eventType() == blpapi.Event.RESPONSE:
            for msg in event:
                securities = msg.getElement("securityData")
                for security in securities.values():
                    fieldData = security.getElement("fieldData")
                    for field in fieldData.elements():
                        url = field.getElementAsString("URL")
                        links.append(url)
        if event.eventType() == blpapi.Event.RESPONSE_TIMEOUT:
            break
        if event.eventType() == blpapi.Event.PARTIAL_RESPONSE:
            continue
        if event.eventType() == blpapi.Event.COMPLETE_RESPONSE:
            break

    return links

if __name__ == "__main__":
    sessionOptions = blpapi.SessionOptions()
    sessionOptions.setServerHost("localhost")
    sessionOptions.setServerPort(8194)

    session = blpapi.Session(sessionOptions)
    session.start()

    subject = "AstraZeneca, Daiichi, Sankyo, Movantik, US"
    pages_min = 1
    pages_max = 5

    full = []
    for page in range(pages_min, pages_max+1):
        links = scrape_bloomberg(subject, page, session)
        full.extend(links)
        print(f"Page {page} completed")

    session.stop()

    with open("results.csv", "w") as f:
        f.write("\n".join(full))

