import json
import os
import re
from datetime import time

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

# result = {"caseId":"", "status":"", "form":"","date":""}
caseStatusStore = {}
caseFinalStore = {}
caseFinalStoreTemp = {}

FinalStatus = {}
def getFinalStatusList():
	with open("final_status_list.json") as jsonFile:
		FinalStatus = json.load(jsonFile)
	return True

with open("final_status_list.json") as jsonFile:
	FinalStatus = json.load(jsonFile)

x_token = ""
def get(caseId, retry, tryTimes):
	if tryTimes > 0:
		if retry > tryTimes:
			print(f"{caseId}:try_failed - {tryTimes}")
			return {caseId, "try_failed", "", ""}

	myClient = requests.Session()
	myClient.max_redirects = 5
	myClient.headers.update({'User-Agent': 'Mozilla/5.0'})
	myClient.headers.update({'Content-Type': 'application/json'})
	myClient.headers.update({'Authorization': 'Bearer ' + x_token})
	myClient.headers.update({'Accept': 'application/json'})
	myClient.headers.update({'Accept-Language': 'en-US'})
	myClient.headers.update({'Accept-Encoding': 'gzip, deflate, br'})
	myClient.headers.update({'Connection': 'keep-alive'})
	myClient.headers.update({'Host': 'egov.uscis.gov'})
	myClient.headers.update({'Origin': 'https://egov.uscis.gov'})
	myClient.headers.update({'Referer': 'https://egov.uscis.gov/casestatus/landing.do'})
	myClient.headers.update({'Sec-Fetch-Dest': 'empty'})
	myClient.headers.update({'Sec-Fetch-Mode': 'cors'})
	myClient.headers.update({'Sec-Fetch-Site': 'same-site'})
	myClient.headers.update({'TE': 'trailers'})
	myClient.headers.update({'X-Requested-With': 'XMLHttpRequest'})

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
		statusPS = re.split(' |,', statusP)
		dateX = ""
		for i, w in enumerate(statusPS):
			if w in MONTHS:
				if dateX == "":
					dateX = statusPS[i] + " " + statusPS[i+1] + ", " + statusPS[i+2]
					break
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
		if i == invalidLimit:
			break

	while low < high:
		mid = (low + high) // 2
		for i in range(invalidLimit):
			if crawler(center, twoDigitYr, day, code, mid+i, format, 0)["status"] != "invalid_num":
				low = mid + 1
				break

		if i == invalidLimit:
			high = mid

	return low - 1

def all(center, twoDigitYr, day, code, format):
	print(f"Run crawler @ {day}")
	last = getLastCaseNumber(center, twoDigitYr, day, code, format)
	print(f"loading {center}-{format}-{twoDigitYr} at day {day}: {last}")

	c = []
	trueLast = 0
	for i in range(last):
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
	for i in range(last):
		if c[i]["status"] == "invalid_num":
			continue
		if c[i]["status"] in FinalStatus:
			newFinalStatusCase[c[i]["caseId"]] = [c[i]["form"], c[i]["date"], c[i]["status"]]
		else:
			caseStatusStore[c[i]["caseId"]] = [c[i]["form"], c[i]["date"], c[i]["status"]]

	print("Merge...")
	caseFinalStore.update(newFinalStatusCase)
	print(f"Done {center}-{format}-{twoDigitYr} at day {day}: {last}")


def main(center, fiscalYear, format, tryN):
	print(time.now())
	print("=================================")
	print(f"Run {center}-{format}-{fiscalYear}, Try = {tryN}")
	print("=================================")

	OK = getFinalStatusList()
	if not OK:
		print("Error: Getting final status list ! Exit...")
		return

	yearDays = 365
	doneN = 0

	dir = os.getcwd()
	print("Working directory:", dir)

	x_token = get_token(dir)
	print(x_token)

	caseFinalStoreFile = f"{dir}/saved_data/{center}_{format}_{fiscalYear}_case_final.json"
	with open(caseFinalStoreFile) as jsonFile:
		caseFinalStore = json.load(jsonFile)
		caseFinalStoreTemp = json.load(jsonFile)

	if format == "LB":
		for day in range(200):
			all(center, fiscalYear, day, 9, "LB")
	elif format == "SC":
		for day in range(yearDays):
			all(center, fiscalYear, day, 5, "SC")

	print("Saving data...")
	case_status_save_path = f"{dir}/saved_data/{center}_{format}_{fiscalYear}.json"
	with open(case_status_save_path, "w") as fp:
		json.dump(caseStatusStore, fp)

	with open(caseFinalStoreFile, "w") as fp:
		json.dump(caseFinalStore, fp)



	print("Done!")

	print(time.now())
	print("=================================")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("center", help="Center code")
	parser.add_argument("fiscalYear", help="Fiscal year")
	parser.add_argument("format", help="Format")
	parser.add_argument("tryN", help="Try times")
	args = parser.parse_args()

	main(args.center, int(args.fiscalYear), args.format, int(args.tryN))




