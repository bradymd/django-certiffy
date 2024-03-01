import dns.resolver
def dnslookup(trial, debug):
  message="DNS for " + trial + ":<br>"
  try:
    ip = dns.resolver.resolve(trial,'A')
    for i in ip:
      message=message + " " + i.to_text() + "<br>"
  except dns.resolver.NoAnswer:
        if debug:
            print("\t[-] No cname "  )
  except dns.exception.Timeout:
        if debug:
            print("\t[-] Timeout")
  except dns.resolver.NXDOMAIN:
        if debug:
            print("[.] Resolved but no entry " )
  except Exception as e:
      message=""

  try:
    cname = dns.resolver.resolve(trial,'CNAME')
    for cn in cname:
      message = message + " " + str(cn.target) +"<br>"
  except dns.resolver.NoAnswer:
        if debug:
            print("\t[-] No cname "  )
  except dns.exception.Timeout:
        if debug:
            print("\t[-] Timeout")
  except dns.resolver.NXDOMAIN:
        if debug:
            print("[.] Resolved but no entry ")
  except Exception as e:
      message=message + ""
  return message
