from bs4 import BeautifulSoup
import httpx
import datetime
from urllib.parse import unquote
from random import randrange, randint
import os
import json

base_dir = os.path.abspath(os.path.dirname(__name__))
data_dir = os.path.join(base_dir, 'data')

def main():
  compute_exchanges_score()
  print("-----------")
  #update_meta_descriptions()
  site_check()
  

def compute_exchanges_score():
  f = open(f'{data_dir}/exchanges_test.json', "r+")
  data = json.load(f)
  for exchange in data['exchanges']:
      score = 0
      if exchange['kyc-type'] == 0:
        score += 2.25
      elif exchange['kyc-type'] == 1:
        score += 1.25
      elif exchange['kyc-type'] == 2:
        score += 0.25
      else:
        score += 0
      if not exchange['custodial']:
        score += 1.0
      if exchange['custodial'] == "semi":
        score += 0.5
      if exchange['no-registration']:
        score += 0.75
      if not exchange['personal-info']:
        score += 2.5
      if exchange['kyc-check']:
        score += 1.75
      if exchange['p2p']:
        score += 1.5
      if exchange['open-source']:
        score += 0.25
      if exchange['tor']:
        score += 0.25
      if exchange['cash']:
        score += 0.5
      if exchange['lnn']:
        score += 0.1
      if not exchange['javascript']:
        score += 0.25
      if score < 7 and exchange['verified']:
        score += 4/score
      if score < 6 and exchange['refunds']:
        score += 3/score
      if score > 10:
        exchange['score'] = 10
      else:
        exchange['score'] = round(score+exchange['score-boost'], 1)

      print(f"{exchange['name']}: {exchange['score']} / {score}")
  f.seek(0)
  json.dump(data, f, indent=2)
  f.truncate()

def update_meta_descriptions():
    with open(f"{data_dir}/exchanges_test.json", "r+") as exchanges:
        data = json.load(exchanges)
        for exchange in data['exchanges']:
            print(f"Requesting {exchange['url']}")
            if "onion" in exchange['url']:
                continue
            if isinstance(exchange['url'], list):
                exchange['url'] = exchange['url'][randint(0, len(exchange['url'])-1)]
            r = httpx.get(exchange['url'])
            soup = BeautifulSoup(r.content, features="html.parser")
            metas = soup.find_all('meta')
            meta_description = [ meta.attrs['content'] for meta in metas if 'name' in meta.attrs and meta.attrs['name'] == 'description' ]
            if meta_description and meta_description != exchange['meta-description']:
                exchange['meta-description'] = meta_description[0]
                
        exchanges.seek(0)
        json.dump(data, exchanges, ident=2)
        exchanges.truncate()
        

# Check ToS
def site_check():    
  keywords = ['kyc', 'aml', 'know your customer', 'money laundering', 'terrorist financing', 'identify user', 'user identification', 'User Identity Verification', 'identity verification', 'user identity', 'provide required personal information', 'provide personal information',
              'KYC requirements', 'AML requirements', 'AML/KYC', 'KYC/AML', 'anti-money laundering', 'U.S. Bank Secrecy Act', 'BSA', '4th AML Directive', 'verify your identity', 'passport', "dirver's license", 'identity card', 'verify your identity', 'identity checks', 'mandatory identification', 'complete our ID verification process',
              'anti-money laundering', 'financing of terrorism', 'know your customer compliance', 'require identity verification']
  
  dom_generated_tos_POTKYC_exchanges = ['KuCoin']  
  kycnotme_cewt = ['TradeOgre', 'RoboSats']
  cfdos_protected = ['TradeOgre']
  
  with open(f"{data_dir}/exchanges_test.json", "r+") as exchanges:
      data = json.load(exchanges)
      print("EDITING LAST CHECK")
      
      for exchange in data['exchanges']:
          if exchange['name'] not in kycnotme_cewt and exchange['name'] not in dom_generated_tos_POTKYC_exchanges and exchange['tos-urls'] and exchange['tos-urls'][0] and exchange['tos-urls'][0] != -1:
              print(f"Exchange: {exchange['name']}")
              for url in exchange['tos-urls']:
                try:
                  r = httpx.get(url)                                
                  soup = BeautifulSoup(r.content, features="html.parser")
                  found_words = []
                  suspicious_ptags = []
                  potential_kyc = False

                  for ptag in soup.find_all('p'):
                      ptag_string = str(ptag)
                      for kw in keywords:
                          if kw in ptag_string:
                              found_words.append(kw)
                              if ptag_string not in suspicious_ptags:
                                suspicious_ptags.append(str(ptag))
                          if len(found_words) >= 2:
                              potential_kyc = True
                except:
                  continue
          else:
              if exchange['tos-urls'] and exchange['tos-urls'][0] == -1 or ".onion" in exchange['url'] or exchange['name'] in kycnotme_cewt:
                  potential_kyc = False
                  
          if exchange['name'] in dom_generated_tos_POTKYC_exchanges:
              potential_kyc = True    
                          
          elif potential_kyc:
              exchange['kyc-check'] = found_words
              exchange['suspicious-tos'] = suspicious_ptags
              exchanges.seek(0)
              json.dump(data, exchanges, indent=2)
              exchanges.truncate()
              print("------ WARNING ------")
              print(
                  f''' Potential KYC on {exchange['name']} ToS. Found words were: \n {found_words}''')
              print("---------------------")
              
          else:
              exchange['kyc-check'] = True
              exchanges.seek(0)
              json.dump(data, exchanges, indent=2)
              exchanges.truncate()

          if "onion" in exchange['url']:
                continue
          if isinstance(exchange['url'], list):
            url = exchange['url'][randint(0, len(exchange['url'])-1)]
          else:
            url= exchange['url']
          r = httpx.get(url)
          exchange['status'] = r.status_code
          if exchange['name'] in cfdos_protected:
            exchange['status'] = 200
          soup = BeautifulSoup(r.content, features="html.parser")
          metas = soup.find_all('meta')
          meta_description = [ meta.attrs['content'] for meta in metas if 'name' in meta.attrs and meta.attrs['name'] == 'description' ]
          if meta_description and meta_description != exchange['meta-description']:
              exchange['meta-description'] = meta_description[0]
              
      data['last_check'] = str(datetime.datetime.today())
      data['exchanges'] = sorted(data['exchanges'], key=lambda k: k['score'], reverse=True)
      exchanges.seek(0)
      json.dump(data, exchanges, indent=2)
      exchanges.truncate()
        
if __name__ == "__main__":
    main()