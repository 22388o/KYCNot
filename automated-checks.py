import ruamel.yaml
from bs4 import BeautifulSoup
import httpx
import datetime
from urllib.parse import unquote
import os

base_dir = os.path.abspath(os.path.dirname(__name__))
data_dir = os.path.join(base_dir, 'data')
yaml = ruamel.yaml.YAML()

def main():
  compute_score()
  #update_meta_descriptions()
  site_check()
  

def compute_score():
  with open(f"{data_dir}/exchanges.yml", "r+") as exchanges:
      data = yaml.load(exchanges)
      for exchange in data['exchanges']:
          score = 0
          if not exchange['may-kyc']:
              score += 2.25
          if not exchange['custodial']:
              score += 1.0
          if not exchange['registration']:
              score += 0.75
          if not exchange['personal-info']:
              score += 2.5
          if exchange['kyc-check']:
              score += 1.75
          if exchange['p2p']:
              score += 1.25
          if exchange['open-source']:
              score += 0.25
          if exchange['tor']:
              score += 0.25
          if score < 7 and exchange['verified']:
              score += 1
          if score < 6 and exchange['refunds']:
              score += 1
          if score > 10:
              exchange['score'] = 10.0
          else:
              exchange['score'] = score+exchange['score-boost']
      exchanges.seek(0)
      yaml.dump(data, exchanges)
      exchanges.truncate()

def update_meta_descriptions():
    with open(f"{data_dir}/exchanges.yml", "r+") as exchanges:
        data = yaml.load(exchanges)
        for exchange in data['exchanges']:
            print(f"Requesting {exchange['url']}")
            if "onion" in exchange['url']:
                continue
            r = httpx.get(exchange['url'])
            soup = BeautifulSoup(r.content, features="html.parser")
            metas = soup.find_all('meta')
            meta_description = [ meta.attrs['content'] for meta in metas if 'name' in meta.attrs and meta.attrs['name'] == 'description' ]
            if meta_description and meta_description != exchange['short-description']:
                exchange['short-description'] = meta_description[0]
                
        exchanges.seek(0)
        yaml.dump(data, exchanges)
        exchanges.truncate()
        

# Check ToS
def site_check():    
  keywords = ['kyc', 'aml', 'know your customer', 'money laundering', 'terrorist financing', 'identify user', 'user identification', 'User Identity Verification', 'identity verification', 'user identity', 'provide required personal information', 'provide personal information',
              'KYC requirements', 'AML requirements', 'AML/KYC', 'KYC/AML', 'anti-money laundering', 'U.S. Bank Secrecy Act', 'BSA', '4th AML Directive', 'verify your identity', 'passport', "dirver's license", 'identity card', 'verify your identity', 'identity checks', 'mandatory identification', 'complete our ID verification process',
              'anti-money laundering', 'financing of terrorism', 'know your customer compliance', 'require identity verification']
  
  dom_generated_tos_POTKYC_exchanges = ['Kucoin']
  
  kycnotme_compilant_exchanges_without_tos = ['Tradeogre']
  
  with open(f"{data_dir}/exchanges.yml", "r+") as exchanges:
      data = yaml.load(exchanges)
      print("EDITING LAST CHECK")
      
      for exchange in data['exchanges']:
          if exchange['tos-urls'][0]:
              print(f"Exchange: {exchange['name']}")
              site = httpx.get(exchange['url'])
              for url in exchange['tos-urls']:
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
                      if len(found_words) >= 2:
                          suspicious_ptags.append(str(ptag))
                          potential_kyc = True
          else:
              if exchange['tos'][0] == -1 or ".onion" in exchange['url']:
                  potential_kyc = False
                  
          if exchange['name'] in dom_generated_tos_POTKYC_exchanges:
              potential_kyc = True    
                          
          elif potential_kyc:
              exchange['kyc-check'] = found_words
              exchange['suspicious-tos'] = suspicious_ptags
              exchanges.seek(0)
              yaml.dump(data, exchanges)
              exchanges.truncate()
              print("------ WARNING ------")
              print(
                  f''' Potential KYC on {exchange['name']} ToS. Found words were: \n {found_words}''')
              print("---------------------")
              
          else:
              exchange['kyc-check'] = True
              exchanges.seek(0)
              yaml.dump(data, exchanges)
              exchanges.truncate()
              
      data['last_check'] = datetime.datetime.today()
      data['exchanges'] = sorted(data['exchanges'], key=lambda k: k['score'], reverse=True)
      exchanges.seek(0)
      yaml.dump(data, exchanges)
      exchanges.truncate()
        
if __name__ == "__main__":
    main()