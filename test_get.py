import requests
import re
from functions import get_token

MONTHS = {
	"January":True, "February":True, "March":     True,
	"April":  True, "May":     True, "June":      True,
	"July":   True, "August":  True, "September": True,
	"October":True, "November":True, "December":  True
}

FormTypes = [
	"I-102", "I-129",  "I-130",	 "I-131", "I-140",  "I-129CW", "I-129F",
	"I-212", "I-290B", "I-360",	 "I-485", "I-485J", "I-526",   "I-539",
	"I-600", "I-600A", "I-601",  "I-601A" "I-612",
	"I-730", "I-751",  "I-751A", "I-765", "I-765V"
	"I-800", "I-800A", "I-817",  "I-821", "I-821D",	"I-824",   "I-829",
	"I-90",  "I-914",  "I-918",	 "I-924", "I-929",
	"EOIR-29", "G-28"]

x_token = ""

def extract_date(string):
    pattern = r"([A-Z][a-z]+) (\d{1,2}), (\d{4})"
    match = re.search(pattern, string)
    if match:
        return match.group()
    else:
        return None

def get(caseId, retry, tryTimes):
	if tryTimes > 0:
		if retry > tryTimes:
			print(f"{caseId}:try_failed - {tryTimes}")
			return {caseId, "try_failed", "", ""}

	myClient = requests.Session()
	myClient.max_redirects = 5
	myClient.headers.update({'User-Agent': 'Mozilla/5.0'})
	myClient.headers.update({'Content-Type': 'application/json'})
	myClient.headers.update({'Authorization': x_token})
	myClient.headers.update({'Connection': 'keep-alive'})
	myClient.headers.update({'Host': 'egov.uscis.gov'})
	myClient.headers.update({'Referer': 'https://egov.uscis.gov'})
	myClient.headers.update({'Sec-Fetch-Dest': 'empty'})
	myClient.headers.update({'Sec-Fetch-Mode': 'cors'})
	myClient.headers.update({'Sec-Fetch-Site': 'same-origin'})

	url_str = "https://egov.uscis.gov/csol-api/case-statuses/"+caseId

	res = myClient.get(url_str)
	if res.status_code != 200:
		# print(f"{caseId}:try_failed - {tryTimes}")
		print(f"Error1: Retry {retry + 1} {caseId}")
		return get(caseId, retry+1, tryTimes)

	res_json = res.json()
	CaseStatusResponse = res_json["CaseStatusResponse"]
	isValid = CaseStatusResponse["isValid"]

	if isValid:
		details_json = CaseStatusResponse["detailsEng"]
		statusH = details_json["actionCodeText"]
		statusP = details_json["actionCodeDesc"]
		formX = details_json["formNum"]
		dateX = extract_date(statusP)
		return {"caseId":caseId, "status":statusH, "form":formX, "date":dateX}
	else:
		return {"caseId":caseId, "status":"invalid_num", "form":"", "date":""}

def test_get():
    global x_token
    x_token = get_token(".")["x_token"]
    caseId = "MSC2400050000"
    retry = 0
    tryTimes = 0
    result = get(caseId, retry, tryTimes)
    assert result == {'caseId': 'MSC2400050000', 'status': 'Case Was Received At Another USCIS Office', 'form': 'I-485', 'date': 'December 21, 2023'}

if __name__ == "__main__":
	test_get()
	print("Everything passed")


