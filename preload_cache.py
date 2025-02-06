#!/usr/bin/env python3
"""
preload_cache.py

A small script that queries our local Flask endpoint /api/airport/<icao>
for a list of airports, forcing them to be cached in airportDb.json.

Usage:
  python preload_cache.py
"""

import requests
import time

# 1) Define your top airports here. (Example: 10 for demo; you could have 1000.)
TOP_AIRPORTS = [
    # --- USA / North America (some major hubs) ---
    "KATL","KDFW","KDEN","KORD","KLAX","KCLT","KPHX","KMCO","KIAH","KLAS",
    "KMIA","KBOS","KSEA","KBWI","KDTW","KMSP","KSLC","KTPA","KMEM","KSAN",
    "KSJC","KAUS","KSMF","KPDX","KCLE","KCMH","KPIT","KMKE","KSNA","KONT",
    "KRDU","KSAT","KSFO","KEWR","KJFK","KLGA","KPHL","KDCA","KIAD","KABQ",
    "KBNA","KSDF","KOAK","KONT","KBUR","KSJC","KSNA","KHNL","KDAL","KIND",
    "KMCI","KMKE","KOXR","KSPS","KELP","KFAT","KMFR","KBDL","KPVD","KSYR",
    "KPWM","KBGR","KMSY","KOMA","KDSM","KFSD","KBOI","KTUS","KTUL","KOKC",
    "KICT","KHSV","KDSM","KGSO","KPNS","KBHM","KSHV","KXNA","KFLL","KPBI",
    "KSAV","KVPS","KMOB","KCRW","KMYR","KCID","KGRR","KFNT","KGRB","KPNS",
    "KBTV","KCHS","KCOS","KGJT","KMTJ","KSGU","KTVC","KBZN","KGTF","KLWS",
    "KBOZ","KIDA","KMSO","KHLN","KBTM","KGCN","KFLG","KRFD","KPIA","KCMI",
    "KDEC","KBMI","KMLI","KCID","KATW","KMSN","KRAP","KCPR","KBIL","KCOD",
    "KGCC","KLAR","KRIW","KWRL","KCYS","KCFO","KFTW","KDAL","KICT","KLAW",
    "KTIK","KDYS","KEND","KADM","KHBR","KHUT","KSPS","KABI","KLRD","KMFE",
    "KCRP","KBRO","KCRS","KCLL","KACT","KGGG","KTYR","KLFK","KBKD","KABI",
    # (Note: Some duplicates may appear—clean up as needed.)

    # --- Canada ---
    "CYYZ","CYVR","CYUL","CYYC","CYOW","CYWG","CYQB","CYEG","CYXE","CYHZ",
    "CYQR","CYSJ","CYFC","CYDF","CYQX","CYFC","CYZS","CYFB","CYTS","CYAM",
    # (etc.)

    # --- Mexico & Central America ---
    "MMMX","MMMY","MMGL","MMUN","MMTY","MMZC","MMSD","MMLP","MMPR","MMSP",
    "MMHO","MMLT","MMCL","MGGT","MHTG","MNMG","MHRO","MSLP","MSJC","MRPV",
    "MRLB","MPTO","MMEP","MMCP",
    # (etc.)

    # --- South America (sample major) ---
    "SBGR","SBGL","SBBR","SBSP","SBKP","SBRF","SBEG","SBBE","SBSV","SBGO",
    "SKBO","MPMG","SPJC","SCEL","SEGU","SEQM","SBRJ","SBBV","SBBH","SBDN",
    "SBFL","SBNF","SBCG","SBCO","SBCP","SPQU","SPRJ","SKRG","SKCL","SKCG",
    # (etc.)

    # --- Europe (lots of major airports) ---
    "EGLL","LFPG","EDDF","EHAM","LEMD","LEBL","LKPR","LOWW","ENGM","ESSA",
    "EKCH","EFHK","ULLI","UUEE","LIRF","LIMC","EDDB","EDDM","EGCC","EGGW",
    "EGSS","LFPO","LFLL","LFBO","LEAL","LEIB","LEAL","LTFM","LTBA","LGAV",
    "LGRP","LCLK","LMML","LDZA","LYBE","LOWI","LOWS","LOWK","LOWG","EETN",
    "EVRA","EYVI","UMMS","UKBB","UKKK","UKOO","UKLL","UKDE","UKDR","LBSF",
    "LBWN","LBBG","LROP","LRCL","LRTR","LHBP","LDSP","LDOS","LYPG","LYNI",
    "LQSA","LWSK","BKPR","LATI","LGKR","LGTS","LGRX","LGKO","LGMT","LGZA",
    # (etc.)

    # All Norwegian airports (for fun)
    "ENZV","ENBR","ENGM","ENBO","ENVA","ENHD","ENAL","ENAT","ENKB","ENML",
    "ENOL","ENGM","ENRY","ENQA","ENRM","ENRO","ENSD","ENSG","ENSH","ENSK",

    # United Kingdom
    "EGKK","EGSS","EGGW","EGCC","EGPH","EGPF","EGPD","EGNT","EGSS","EGLC",


    # --- Africa (selected major airports) ---
    "FAOR","FACT","FALE","FALA","FQMA","FVHA","FVRG","FBSK","FBMN","FLKK",
    "FZAA","FZNA","FCPP","FCBB","FOOL","FOON","FTTJ","FTTA","FEFF","FKKD",
    "FKYS","DBBB","DGAA","DIAP","DNAA","DNMM","DGSI","DNPO","DTTA","DTMB",
    "HECA","HEAX","HELX","HESN","HKJK","HKMO","HRYR","HRYG","HTDA","HTKJ",
    "HUEN","HBBA","HSSS","HSRJ","GMFF","GMMN","GMME","GOBD","GUCY","GFLL",
    # (etc.)

    # --- Middle East ---
    "OMDB","OTHH","OKBK","OEDF","OERK","OEJN","OIII","OIMM","OIFM","OIKB",
    "OJAI","LLBG","LLHA","HECA","HEOC","HELX","HKIS","OEAB","OBBI","OMSJ",
    "OMAA","OMAD","OMAL","OPKC","OPIS","OPLA","VCBI","VECC","VIDP","VABB",
    "VOBL","VOMM","VOHS","VOCI","VAAH","VANP","VOGO","VEPT","VEJT","VRMM",
    # (etc.)

    # --- Asia (major hubs) ---
    "RJTT","RJAA","RJCC","RJBB","ROAH","RJSF","RJSS","RJFK","RJOH","ZBAA",
    "ZSPD","ZGGG","ZHHH","ZUUU","ZUCK","ZUCK","ZJSY","ZSHC","ZSOF","ZBTJ",
    "VHHH","RCTP","RCSS","RCMQ","RCBS","ZBHH","ZBOW","RKSI","RKSS","RKPC",
    "RKTN","RCKH","RODN","RJFU","RJOM","RJAF","RJCA","RJEB","RJCH","RJFR",
    "RJSN","RJNK","RJGG","ROIG","RJFU","RJBE","RJFK","RJCK","RJNT","RJTH",
    "RJTK","RJDT","RJEC","RJEO","ROAH","RJDA","RJAW","RJKA","RJKN","RJKB",
    "RJFU","WIII","WIII","WADD","WMKK","WMKP","WMKL","VTBS","VTBD","VTCC",
    "VTSP","VVNB","VVTS","VVCR","VVDN","WSSS","WSAP","WSAC","VTBU","VTSG",
    # (etc.)

    # --- Australia / Oceania ---
    "YSSY","YMML","YBBN","YPAD","YPDN","YPPH","YBCG","YSCB","NZAA","NZCH",
    "NZWN","NFFN","NGFU","NFNA","NSTU","NTAA","PHNL","PHKO","PHLI","PHOG",
    "PJON","PKMJ","PKWA","PLCH","PWAK","NVVV","AGGH","ANYN","AYPY","AYMD",
    "AYTJ","AYGA",
    # (etc.)

    # ... You can keep adding up to 1000, merging major airports from each continent ...
    #
    # The idea is just to accumulate a big list of any airports you want pre-cached.
    # Remember you have 3000 daily queries limit on CheckWX, so 1000 entries is feasible
    # if you only do it once or very infrequently.
]

# 2) The base URL of your local Flask app
BASE_URL = "https://home.chulak.io"

def main():
    total_airports = len(TOP_AIRPORTS)
    print(f"Preloading airport cache for {total_airports} airports...")

    for i, icao in enumerate(TOP_AIRPORTS, start=1):
        icao = icao.strip().upper()
        url = f"{BASE_URL}/api/airport/{icao}"
        print(f"[{i}/{total_airports}] GET {url}")

        try:
            resp = requests.get(url, timeout=10)
        except requests.RequestException as e:
            print(f"  => ERROR: Request failed for {icao}: {e}")
            continue

        if resp.status_code == 200:
            data = resp.json()
            # We have the full station record now
            print(f"  => OK: Stored {icao} with data keys {list(data.keys())}")
        else:
            # Possibly 404 or something else
            print(f"  => ERROR: {icao} returned {resp.status_code} - {resp.text}")

        # OPTIONAL: a small sleep to avoid spamming. Usually not needed if your local app
        # is robust, but if CheckWX has rate-limits, the local app might queue them quickly.
        # time.sleep(0.3)

    print("Done preloading cache!")


if __name__ == "__main__":
    main()