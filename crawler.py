import copy
import json
import os
import random
import re
import time
from datetime import datetime

from functions import get_token

import requests

import argparse

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

doneN = 0
# result = {"caseId":"", "status":"", "form":"","date":""}
caseStatusStore = {}
caseFinalStore = {}
caseFinalStoreTemp = {}

FinalStatus = {}
def getFinalStatusList():
	global FinalStatus
	with open("final_status_list.json") as jsonFile:
		FinalStatus = json.load(jsonFile)
	return True
def extract_date(string):
    pattern = r"([A-Z][a-z]+) (\d{1,2}), (\d{4})"
    match = re.search(pattern, string)
    if match:
        return match.group()
    else:
        return None

x_token = ""
def get(caseId, retry, tryTimes):
	global x_token
	if tryTimes > 0:
		if retry > tryTimes:
			print(f"{caseId}:try_failed - {tryTimes}")
			return {caseId, "try_failed", "", ""}

	user_agent_list = [
		"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0;) Gecko/20100101 Firefox/61.0",
		"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
		"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
		"Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
	]
	ua =  random.choice (user_agent_list)
	# ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

	with requests.Session() as myClient:
		myClient.headers.update({'User-Agent': ua})
		myClient.headers.update({'Accept': '*/*'})
		myClient.headers.update({'Accept-Encoding': 'gzip, deflate, br'	})
		myClient.headers.update({'Accept-Language': 'en-US,en;q=0.9'})
		myClient.headers.update({'Content-Type': 'application/json'})
		myClient.headers.update({'Authorization': x_token})
		myClient.headers.update({'Connection': 'close'})

		url_str = "https://egov.uscis.gov/csol-api/case-statuses/"+caseId
		res = myClient.get(url_str)

	# print(res.status_code)
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


	# (1) Valid
	# {
	# 	"CaseStatusResponse": {
	# 		"receiptNumber": "IOE0911023658",
	# 		"isValid": true,
	# 		"detailsEng": {
	# 			"formNum": "I-765",
	# 			"formTitle": "Application for Employment Authorization",
	# 			"actionCodeText": "Card Was Delivered To Me By The Post Office",
	# 			"actionCodeDesc": "On May 18, 2021, the Post Office delivered your new card for Receipt Number IOE0911023658, to the address that you gave us.  The tracking number assigned is 9205590179168812731640.  You can use your tracking number at <a href='https://tools.usps.com/go/TrackConfirmAction_input?origTrackNum=9205590179168812731640' target='_blank'>www.USPS.com</a> in the Quick Tools Tracking section.  If you move, go to <a href=\"https://egov.uscis.gov/coa/displayCOAForm.do\" target=\"_blank\">www.uscis.gov/addresschange</a> to give us your new mailing address.",
	# 			"empty": false
	# 		},
	# 		"detailsEs": {
	# 			"formNum": "I-765",
	# 			"formTitle": "Solicitud de Autorización de Empleo",
	# 			"actionCodeText": "Tarjeta Me Fue Entregada Por El Servicio Postal De EE.UU.",
	# 			"actionCodeDesc": "El 18 de Mayo de 2021, la oficina de correos entregó su nueva tarjeta para su Número de Recibo IOE0911023658, a la dirección que nos proporcionó.  El número de seguimiento asignado es 9205590179168812731640.  Puede usar su número de seguimiento en www.USPS.com en la sección de Herramientas rápidas de seguimiento.  Si cambia de domicilio, visite <a href=\"https://egov.uscis.gov/coa/displayCOAForm.do\" target=\"_blank\">www.uscis.gov/addresschange</a> para notificarnos su nueva dirección postal.",
	# 			"empty": false
	# 		}
	# 	}
	# }
	#
	# (2) Invalid
	# {"CaseStatusResponse":{"receiptNumber":"MSC2390000000","isValid":false}}

def buildURL(center, twoDigitYr, day, code, caseSerialNumbers, format):
	if format == "SC":
		return f"{center}{twoDigitYr}{day:03d}{code}{caseSerialNumbers:04d}"
	else:
		return f"{center}{twoDigitYr}{code}{day:03d}{caseSerialNumbers:04d}"

def crawler(center, twoDigitYr, day, code, caseSerialNumbers, format, tryTimes):
	urlX = buildURL(center, twoDigitYr, day, code, caseSerialNumbers, format)
	res = get(urlX, 0, tryTimes)
	return res

def getLastCaseNumber(center, twoDigitYr, day, code, format):
	print(f"Geting last @ {day}")
	low = 1
	high = 1
	invalidLimit = 10

	i = 0
	while high < 10000:
		for i in range(invalidLimit):
			if crawler(center, twoDigitYr, day, code, high+i-1, format, 0)["status"] != "invalid_num":
				high *= 2
				break
		if i == invalidLimit-1:
			break

	while low < high:
		mid = (low + high) // 2
		for i in range(invalidLimit):
			if crawler(center, twoDigitYr, day, code, mid+i, format, 0)["status"] != "invalid_num":
				low = mid + 1
				break

		if i == invalidLimit-1:
			high = mid

	return low - 1

def all(center, twoDigitYr, day, code, format):
	print(f"Run crawler @ {day}")
	last = getLastCaseNumber(center, twoDigitYr, day, code, format)
	print(f"loading {center}-{format}-{twoDigitYr} at day {day}: {last}")

	c = []
	trueLast = 0
	global caseFinalStoreTemp
	global FinalStatus
	global caseStatusStore
	global caseFinalStore
	global doneN

	for i in range(last+1):
		if format == "SC":
			caseId = f"{center}{twoDigitYr}{day:03d}{code}{i:04d}"
		else:
			caseId = f"{center}{twoDigitYr}{code}{day:03d}{i:04d}"
		if caseId in caseFinalStoreTemp:
			continue
		trueLast += 1
		c.append(crawler(center, twoDigitYr, day, code, i, format, 0))

	print("Asyc......")
	newFinalStatusCase = {}
	for xi in c:
		if xi["status"] == "invalid_num":
			continue
		if xi["status"] in FinalStatus:
			newFinalStatusCase[xi["caseId"]] = [xi["form"], xi["date"], xi["status"]]
		else:
			caseStatusStore[xi["caseId"]] = [xi["form"], xi["date"], xi["status"]]

	print("Merge...")
	doneN += 1
	caseFinalStore.update(newFinalStatusCase)
	print(f"Done {center}-{format}-{twoDigitYr} at day {day}: {last}")


def main(center, fiscalYear, format, tryN):
	print( datetime.now())
	print("=================================")
	print(f"Run {center}-{format}-{fiscalYear}, Try = {tryN}")
	print("=================================")

	OK = getFinalStatusList()
	if not OK:
		print("Error: Getting final status list ! Exit...")
		return

	yearDays = 365
	global doneN
	doneN = 0

	dir = os.getcwd()
	print("Working directory:", dir)

	global x_token
	x_token = get_token(dir)["x_token"]
	print(x_token)

	caseFinalStoreFile = f"{dir}/saved_data/{center}_{format}_{fiscalYear}_case_final.json"
	global caseFinalStore
	global caseFinalStoreTemp
	with open(caseFinalStoreFile) as jsonFile:
		caseFinalStore = json.load(jsonFile)
		caseFinalStoreTemp = copy.deepcopy(caseFinalStore)

	global caseStatusStore
	caseStatusStore = {}

	if format == "LB":
		for day in range(200):
			all(center, fiscalYear, day, 9, "LB")
	elif format == "SC":
		for day in range(1,yearDays):
			all(center, fiscalYear, day, 5, "SC")

	print("Saving data...")
	case_status_save_path = f"{dir}/saved_data/{center}_{format}_{fiscalYear}.json"
	with open(case_status_save_path, "w") as fp:
		json.dump(caseStatusStore, fp)

	with open(caseFinalStoreFile, "w") as fp:
		json.dump(caseFinalStore, fp)



	print("Done!")

	print( datetime.now())
	print("=================================")

if __name__ == "__main__":
	# parser = argparse.ArgumentParser()
	# parser.add_argument("center", help="Center code")
	# parser.add_argument("fiscalYear", help="Fiscal year")
	# parser.add_argument("format", help="Format")
	# parser.add_argument("tryN", help="Try times")
	# args = parser.parse_args()

	# main(args.center, int(args.fiscalYear), args.format, int(args.tryN))
	main("MSC", 24, "SC", 100)



