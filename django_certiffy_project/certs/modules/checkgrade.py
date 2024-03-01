import requests, json, sys, socket, time, logging, re
import urllib3


def grade_ssllabs(hostname):
    logging.debug("grade_ssllabs")
    cert = {"url": hostname, "port": "443"}
    # ssllabs can only scan port 443
    try:
        ipAddress = socket.gethostbyname(hostname)
    except:
        logging.debug("host %s gethostyname error" % (hostname))
        message="DNS issue?"
        return False, "N", message
    # Check host is up  here eventually
    url = (
        "https://api.ssllabs.com/api/v3/analyze?host="
        + hostname
        + "&s="
        + ipAddress
        + "&startNew=on&ignoreMismatch=on&all=done&hideResults=on"
    )
    urllib3.disable_warnings()


    # Lets try  2 times here, have to give up after 3
    count = 1
    while True:
      if count < 4:
        try:
            response = requests.get(url, verify=False)
            if response.ok:
                break
        except    ConnectionError as err:
            logging.debug(f'{err}')
            messsage=f'{err}'
            return False,"N",message
        except Exception as  err:
            logging.debug(f'count={count} {url} {err}')
        count = count + 1
      else:
        message=f'{count} retries, giving up'
        return False,"N",message

    # we can still get empty response fields here and I dont know why particulary 529 shows in debug
    try:
        j = response.json()
        logging.debug(f'response.status_code {response.status_code}')
        if "full capacity" in j: 
            message = 'Running at full capacity. Please try again later.'
            return False,"N",message
    except Exception as err:
        message=err
        return False,"N",message
    # so if j isnt populated, anything going forward from here would break


    count = 1
    sleep_count = [60, 60, 30, 20, 10]
    while j["status"] == "IN_PROGRESS" or j["status"] == "DNS":
        if count < 5:
            sleep = sleep_count[count]
        else:
            sleep = 10
        logging.debug(
            "host %s, status %s, sleep %s, count %d"
            % (hostname, j["status"], sleep, count)
        )
        time.sleep(sleep)
        count = count + 1
        url = (
            "https://api.ssllabs.com/api/v3/analyze?host="
            + hostname
            + "&s="
            + ipAddress
            + "&fromCache=on&ignoreMismatch=on&all=done"
        )
        # not sure about this here
        try:
            response = requests.get(url, verify=False)
            if count > 33:
                return False, "N", "Taking too long,  giving in"
            if not response.ok:
                continue
        except:
            pass
        try:
            j = response.json()
        except JSONDecodeError as jsonerr :
            loggin.debug(f'variable j is {j}')
            j= {"statusMessage": "JSONDecodeError try again"}

    #logging.debug('host %s : %s' % (hostname, j ))
    try:
        j["statusMessage"]
        if (
            j["statusMessage"] == "Unable to connect to the server"
            or j["statusMessage"] == "Unable to resolve domain name"
            or j["statusMessage"] == "No secure protocols supported"
            or j["statusMessage"] == "JSONDecodeError try again"
        ):
            logging.debug("host %s, is not public " % hostname)
            message=j["statusMessage"]
            return False, "N", message
    except:
        pass
   
    # at this point it should be status READY and should an endpoint
    try:
        e = j["endpoints"]
        endpoints = e[0]
        if  ( endpoints["statusMessage"] == "Unable to connect to the server"
            or endpoints["statusMessage"] == "Unable to resolve domain name"
            or endpoints["statusMessage"] == "No secure protocols supported"
        ):
            logging.debug("host %s, is not public " % hostname)
            message=j["statusMessage"] + " is not publicly accessible"
            return False, "N", message
    except:
        pass

    # from here there should be  endpoints
    try: 
        endpoints["grade"]
        message=""
        return True,endpoints["grade"] ,message
    except:
        #message="undetermined problem found"
        message=endpoints["statusMessage"]
        return False,"N",message

