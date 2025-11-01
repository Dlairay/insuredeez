we are building an agent orchestration using google-adk to design the agents. rag_agent is not part of this orchestration, the only file i actually need from rag_agent is Taxonomy_Filled.json this file must never be modified, it serves as one of the grounding resources. 

the entire agent orchestration revolves around utilising the template from backend/ai_backend/schema_template.py the idea is that upon use account creation, an empty template is initialised, and is filled along the pipeline. 

the high level architecture is that the conversation agent acts as the user facing chatbot, while calling upon helper agents and tools to fill up the pipeline from information during the session. 

conversation agent will have 3 helper agents:
1. document magic agent
    responsible for transforming base 64 image of passport, id and itinerary to fill up what it can about in this section of the schema.  "tripType": "",
  "departureDate": "",
  "departureCountry": "",
  "arrivalCountry": "",
  "adultsCount": 0,
  "childrenCount": 0,

  "insureds": [
    {
      "id": "",
      "title": "",
      "firstName": "",
      "lastName": "",
      "nationality": "",
      "dateOfBirth": "",
      "passport": "",
      "email": "",
      "phoneType": "",
      "phoneNumber": "",
      "relationship": ""
    }
  ],

  "mainContact": {
    "id": "",
    "title": "",
    "firstName": "",
    "lastName": "",
    "nationality": "",
    "dateOfBirth": "",
    "passport": "",
    "email": "",
    "phoneType": "",
    "phoneNumber": "",
    "address": "",
    "city": "",
    "zipCode": "",
    "countryCode": ""
  }
  it is crucial that all the fields gets filled up, you have to prompt the parent agent to prompt the user to give information about the missing fields,not one by one but in one go, the AI llm should be smart enough to match the fields. this information will be used to make api calls to 2 endpoints.
Firstly >  curl --location 'https://dev.api.ancileo.com/v1/travel/front/pricing' \
--header 'Content-Type: application/json' \
--header 'x-api-key: XXXXXXXXXXXXXX' \
--data '{
"market": "SG",
"languageCode": "en",
"channel": "white-label",
"deviceType": "DESKTOP",
"context": {
"tripType": "ST",
"departureDate": "2025-11-01",
"returnDate": "2025-11-15",
"departureCountry": "SG",
"arrivalCountry": "CN",
"adultsCount": 1,
"childrenCount": 0
}
}'
note that the fields "market": "SG",
"languageCode": "en",
"channel": "white-label",
"deviceType": "DESKTOP", are hardcoded, we just need to fill the rest by pulling information from the user object

it should return something like 'id': '613d6afb-d34c-43aa-80fc-05eede925c61', 'languageCode': 'en', 'offerCategories': [{'productType': 'travel-insurance', 'defaultSelectedOffer': None, 'optOutLabel': None, 'optOutEltClass': 'velocity-travel-insurance-out', 'offers': [{'id': '22539aa6-5abe-4bfb-9156-35d4e1a77cfd', 'productCode': 'SG_AXA_SCOOT_COMP', 'unitPrice': 17.6, 'priceBreakdown': {'priceExc': 17.6, 'priceInc': 17.6, 'totalTaxes': 0, 'paxSplit': [], 'otherTaxesSplit': 0, 'commissions': {}, 'priceNoDiscountExc': 17.6, 'priceNoDiscountInc': 17.6, 'priceNoDiscount': 17.6, 'discount': {'value': 0, 'is_percentage': 1}, 'salesTax': 0, 'stampDuty': 0, 'otherTaxes': []}, 'coverDates': {'from': '2025-11-01', 'to': '2025-11-15'}, 'coverDateTimes': {'from': '2025-11-01T00:00:00+00:00', 'to': '2025-11-15T23:59:59+00:00'}, 'currency': 'SGD', 'optInEltClass': 'velocity-travel-insurance-22539aa6-5abe-4bfb-9156-35d4e1a77cfd-in', 'productInformation': {'title': 'Scootsurance - Travel Insurance', 'description': '{\n    "heading": "Scootsurance",\n    "subheading": "Underwritten by MSIG Insurance (Singapore) Pte Ltd",\n    "benefits": {\n        "heading": "We\'ve got you covered even in difficult times... now enhanced with Covid-19 benefits!",\n        "benefitList": [\n            {"title": "Trip cancellation / curtailment", "tooltip": "Your irrecoverable travel fare and accommodation will be reimbursed up to the Sum Insured if you have to cancel/curtail your trip due to covered reasons such as being infected with Covid-19."},\n            {"title": "Overseas hospitalization / quarantine allowance", "tooltip": "Receive a daily cash benefit if you\'re hospitalized/quarantined due to Covid-19."},\n            {"title": "Overseas medical expenses", "tooltip": "Enjoy your trip to the fullest knowing that you will be covered up to the Sum Insured for overseas medical expenses incurred due to an accidental bodily injury or sickness, including Covid-19."},\n            {"title": "Medical evacuation / repatriation", "tooltip": "You can count on us in the event that you are in an emergency medical situation and need to be moved to another location to receive urgent treatment or to be repatriated to Singapore."},\n            {"title": "24/7 emergency medical assistance hotline", "tooltip": "We are here for you round-the-clock! You can call the MSIG Assist 24-hour hotline in the event that you are in an emergency medical situation."},\n            {"title": "24/7 travel assistance hotline", "tooltip": "You can call the MSIG Assist 24-hour hotline at any time for travel assistance."}\n        ]\n    },\n    "selection": {\n        "heading": "<p>*Covid-19 benefits will become null and void if you, family member, traveling companion or the family you are staying with during the trip is already infected with Covid-19 at the point of purchase or you are commencing a trip against any government\'s travel advisory. Trip cancellation cover does not apply in the event of a travel ban due to Covid-19.</p><a class=\'external-link\' target=\'_blank\' href=\'https://static.dev.wl.ancileo.com/axa/scoot/sg/doc/Scootsurance_Table_of_benefits.pdf\'>Click here</a> to view the complete table of benefits! <br/><br/>Why tango with lady luck when you can have <b>Scootsurance</b>?",\n        "options": {\n            "yes": "Yes, I would like to be protected by Scootsurance! I accept the <a class=\'external-link\' target=\'_blank\' href=\'https://static.dev.wl.ancileo.com/axa/scoot/sg/doc/PolicyWording.pdf/\'>terms & conditions</a> and <a class=\'external-link\' target=\'_blank\' href=\'https://www.msig.com.sg/privacy-cookies-policy/\'>privacy policy.</a>",\n            "no": "No, I\'ll take my chances."\n        }\n    },\n    "supportMessage": "<a class=\'external-link\' target=\'_blank\' href=\'https://static.dev.wl.ancileo.com/axa/scoot/sg/doc/Scootsurance_Table_of_benefits.pdf\'>Click here</a> to view the complete table of benefits! <br/><br/><p>Scootsurance is covered under the Policy Owners\' Protection Scheme which is administered by the Singapore Deposit Insurance Corporation (SDIC). Coverage for your policy is automatic and no further action is required from you. For more information on the types of benefits that are covered under the scheme as well as the limits of coverage, where applicable, please contact your insurer or visit the GIA/LIA or SDIC websites (<a class=\'external-link\' target=\'_blank\' href=\'https://www.gia.org.sg/\'>www.gia.org.sg</a> or <a class=\'external-link\' target=\'_blank\' href=\'https://www.lia.org.sg/\'>www.lia.org.sg</a> or <a class=\'external-link\' target=\'_blank\' href=\'https://www.sdic.org.sg/\'>www.sdic.org.sg</a>).</p>",\n    "inPartnershipWith": "<img src=\'https://static.dev.wl.ancileo.com/axa/scoot/sg/images/msig_logo.png\' /><br/>",\n    "tableofBenefitsPdfUrl": "https://static.dev.wl.ancileo.com/axa/scoot/sg/doc/Scootsurance_Table_of_benefits.pdf",\n    "insuranceProvider": "AXA"\n}', 'imageURL': None, 'benefits': '', 'optInLabel': None, 'attributes': {'attribute1': 'Scootsurance - Travel Insurance'}, 'tcsUrl': 'https://static.dev.wl.ancileo.com/axa/scoot/sg/doc/PolicyWording.pdf/', 'datasheetUrl': '', 'contractProductCode': None, 'minBookingClass': None, 'maxBookingClass': None, 'isRenewable': 0, 'extras': []}, 'options': []}]}]}

secondly>  curl --location 'https://dev.api.ancileo.com/v1/travel/front/purchase' \
--header 'Content-Type: application/json' \
--header 'X-API-Key: XXXXXXXXXX' \
--data-raw '{
"market": "SG",
"languageCode": "en",
"channel": "white-label",
"quoteId": "9473a27b-7c46-4870-9e33-aea613942d28",
"purchaseOffers": [
{
"productType": "travel-insurance",
"offerId": "f80dfc75-36e3-433a-b561-f182383cd342",
"productCode": "SG_AXA_SCOOT_COMP",
"unitPrice": 17.6,
"currency": "SGD",
"quantity": 1,
"totalPrice": 17.6,
"isSendEmail": true
}
],
"insureds": [
{
"id": "1",
"title": "Mr",
"firstName": "John",
"lastName": "Doe",
"nationality": "SG",
"dateOfBirth": "2000-01-01",
"passport": "123456",
"email": "john.doe@gmail.com",
"phoneType": "mobile",
"phoneNumber": "081111111",
"relationship": "main"
}
],
"mainContact": {
"id": "1",
"title": "Mr",
"firstName": "John",
"lastName": "Doe",
"nationality": "SG",
"dateOfBirth": "2000-01-01",
"passport": "123456",
"email": "john.doe@gmail.com",
"phoneType": "mobile",
"phoneNumber": "081111111",
"address": "12 test test 12",
"city": "SG",
"zipCode": "12345",
"countryCode": "SG"
}
}' 
with these fields also pulled from the quotation endpoint
 "market": "SG",
"languageCode": "en",
"channel": "white-label",
"quoteId": "9473a27b-7c46-4870-9e33-aea613942d28",
"purchaseOffers": [
{
"productType": "travel-insurance",
"offerId": "f80dfc75-36e3-433a-b561-f182383cd342",
"productCode": "SG_AXA_SCOOT_COMP",
"unitPrice": 17.6,
"currency": "SGD",
"quantity": 1,
"totalPrice": 17.6,
"isSendEmail": true
}
],
The purchase endpoint should only be called after payment has been successfully
processed
○
This point must be discussed to mock it !
Ensure all dates are in YYYY-MM-DD format
All timestamps should follow ISO 8601 format
The quoteId and offerId must be obtained from a prior quotation request


<!-- 2. policy recommendation agent
this agent has sub agents as well(so its conversation_agent>policy>recommendation_agent>{name}_agent), 

-needs agent
 creates list of needs from the itinerary, it looks at this section of the profile, and flips the things it found in the itinerary to True for the conditions in the profile data structure artifact:
  taxonomy_dict = {
  "needs": {
    "24hours_emergency_medical_assistance":False,
    "24hours_travel_assistance":False,
    "HIV_AIDS_conditions":False,
    "ICU_hospitalisation_outside_singapore":False,
    "TCM_expenses":False,
    "accidental_death_permanent_disablement":False,
    "accidental_loss_or_damage_to_rental_vehicle":False,
    "activities_covered":False,
    "actual_telephone_charges_requirement":False, .........}}

 -->


the rough guideline of what each agent should do is in their respective objective.md files if present. if there is a huge clash in logic of what i have defined here and in the objective.md, the instructions here take priority. 