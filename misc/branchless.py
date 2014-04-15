# -*- coding: UTF-8 -*-

"""
Her prøver jeg å se på hvilke primitiver vi må støtte i flow table for å
kunne implementere ACCEPT/LEARN-algoritmene i Paxos.

Poenget er at flow tables skal være lynkjappe å kjøre. Derfor hadde det vært
nice om vi kan benytte BRANCHLESS kode (dvs ingen JMPs som JNE osv, eller
ingen IF-statements). Da kan man fylle opp instruction pipeline så mye man
orker og tute og kjøre.

Det aller beste hadde vært å ha ting 100% statisk (tenk, bitfields og
O(1)-operasjoner), men det går nok ikke.

Her prøver jeg ut noen ting i enkel python-kode.
"""

def do_nothing(**kw):
  print("!(n >= rnd) " + str(kw))

def n_gt_rnd(n, rnd):
  """Is n >= rnd?"""
  # if n >= rnd, then (n-rnd)>=0 --- ikke godt nok
  # if n < rnd, then (n-rnd)<0 --- godt nok og basis for test
  result = {True:0, False:1}
  return result[ (n - rnd) < 0 ]
  # dette er i prinsippet en CMP.. vet ikke hvor mange cycles det er,
  # men mer en bitsjekk

def if_n_gt_rnd(n, rnd, func):
  """Kall func hvis n >= rnd."""
  call = {0: do_nothing, 1: func}
  call[ n_gt_rnd(n, rnd) ](n=n, rnd=rnd)

def learned(**kw):
  print("  n >= rnd  " + str(kw))

def test():
  for n in range(0,5):
    for rnd in range(0,5):
      result = n_gt_rnd(n, rnd)
      if n >= rnd:
        check = 1
      else:
        check = 0

      if result == check:
        msg = "OK  "
      else:
        msg = "FAIL"

      print("%s n=%d rnd=%d: " % (msg, n, rnd)),
      if_n_gt_rnd(n, rnd, learned)

if __name__ == "__main__":
  test()

"""
KONKLUSJON:
Som en ser over så kan man effektivt implementere en BRANCHLESS test av
on_accept sjekken

    if n >= rnd then ....

med å gjøre sånt i pseudo-assembly:
http://en.wikibooks.org/wiki/X86_Assembly/Control_Flow#Comparison_Instructions

    001 
    100 CMP n, rnd
    200 JMP ZF*100 + 300 # noe i den duren, kan vel bruke EIP m/offset eller noe
    300 <BODY of IF-clause>
    399 JMP 900
    400 <BODY of ELSE-clause>
    500 JMP 900
    ...
    900 <AFTER the IF-THEN-ELSE block>

MEN vi har et problem.. for JMP er også en branch... fuckit
Det samme er et funksjonskall egentlig...

Se også denne:

  http://stackoverflow.com/questions/6133322/what-does-a-branchless-if-in-c-look-like

Det skal være mulig altså...
Men står også der at vi egentlig kan drite i det..
Fett.. poenget er at dette kan faktisk gå kjapt

(motivasjonen min var å bruke branchless-triksa fra gamle shader-språk, der
en ganger en verdi, altså

  c = cmp a, b
  d = c*true_value + (1-c)*false_value

eller hvordan det var
"""
