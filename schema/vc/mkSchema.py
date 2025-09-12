#! /bin/python3

import sys
import json
from pathlib import Path


def loadJSON(json_file):
   with open(json_file) as json_file:
     return json.load(json_file)

def p(message, writetolog=False):
   if writetolog:
      write_log(message)
   else:
      print(message)
    
def pj(the_json, writetolog=False):
    p(json.dumps(the_json, indent=4, sort_keys=False), writetolog)


def write_file(contents, filepath, mkpath=True, overwrite=False, type='txt'):
   if mkpath:
      Path(filepath).mkdir(parents=True, exist_ok=overwrite)

   if overwrite:
      f = open(filepath, "w")
   else:
      f = open(filepath, "a")

   match type:
    case 'yaml':
         yaml.preserve_quotes = True
         yaml.dump(contents, f)
    case 'json':
         f.write(json.dumps(contents,sort_keys=False, indent=4, ensure_ascii=False,separators=(',', ':')))
    case _:
         # assume text
         f.write(contents+"\n")
   
   f.close()

def replace_capitals(s):
    return ''.join(['' + ("_" + char.lower()) if char.isupper() else char for char in s]).strip()

def covert_schemaname(attributeName):
   # Attributes need to be rename to claims
   # as a general rule of thumb:
   #
   # eduPerson, voPerson and Schac schema names are just lowercased ad get added an underscore
   #
   # for the attrbute name: if a captical is found, it is replaced with a lower and prefixed with an underscore.
   #
   # sp eduPersonScopedAffiliation becomes: eduperson_scoped_affiliation
   # 
   s= attributeName

   if s.startswith('eduPerson'):
      return ("eduperson" + fixName(replace_capitals(s[9:])))
   elif s.startswith('voPerson'):
      return ("voperson" + fixName(replace_capitals(s[8:])))
   elif s.startswith('Schac'):
      return ("schac" + fixName(replace_capitals(s[5:])))
   else:
      return (fixName(replace_capitals(s)))

def fixName(name):
   return name.replace("_i_d", "_id").replace("_d_n", "_dn").replace("_u_r_i", "_uri").replace("_s_m_i_m_e", "_smime")

def mapType(equality, multivalued = False):
   p(equality)
   if not multivalued:
      match equality:
         case "caseExactMatch" | "caseIgnoreMatch" | "distinguishedNameMatch" | "octetStringMatch":
            return "string"
         case "integerMatch":
            return "integer"     
         case "numericStringMatch":
            return "number"
   else:
      return None        

def main(argv):
   schemaFile = "vo_person_2_0_0.json"

   schema = { 
      "$id": "https://refeds.org/schemas/vc/vo_person_2_0_0.json",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$comment": "This schema implements voPerson version 2.0.0 (19 May 2022) - https://refeds.org/specifications/voperson - This schema is maintained by REFEDs (https://refeds.org). The mission of REFEDS (the Research and Education FEDerations group) is to be the voice that articulates the mutual needs of research and education identity federations worldwide.",
      "title": "voPersonCredentials",
      "description": "Schema for verifiable credential claims describing a user in the context of voPerson",
      "type": "object",
      "properties": {
         "credentialSubject": {
            "type": "object",
            "properties": {}
         }
      }
   }

   # Generate object properties based on ldif schema,coverted to json by chatGTP
   # The resulting schac_ldif.json was added for reference
   #
   schemaJSON = loadJSON('voperson_ldif.json')
   pj(schemaJSON)
   
   object_props = {}
   att = schemaJSON['olcAttributeTypes']

   for a in att:
      name = covert_schemaname(a['NAME'])
      object_props[name] = {
         "type": mapType(a['EQUALITY'], ('singleValue' in a)),
         "oid": a['oid'],
         "description": a['DESC'],
      }

      # TODO: validate these
      # TODO: we still have several format and pattern definitions missing
      match a['NAME']:
         case "voPersonAffiliation" | "voPersonExternalAffiliation" |"voPersonScopedAffiliation" :
            object_props[name]['type'] = "string"
            object_props[name]['pattern'] =  "^\\S+@\\S+\\.\\S+$"

         case "voPersonVerifiedEmail":
            object_props[name]['type'] = "email"

   schema["properties"]["credentialSubject"]["properties"] = object_props
   write_file(schema, schemaFile, mkpath=False, overwrite=True, type='json')

if __name__ == "__main__":
   main(sys.argv[1:])