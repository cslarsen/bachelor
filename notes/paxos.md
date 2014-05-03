Paxos på controller
===================

Først få opp ethernet-meldinger.
Vi bruker et abstrakt inteface først, så kan dette bruke OFP om
hensiktsmessig senere.

Vi må vite om de andre switchene sine ethernet-adresser.

eth type=0x7a 0x05 ("paxos")

flow: hvis type=0x7a05, upcall (hello msg)
      hvis type=0x7a0?, run bytecode (if-then-else, osv)

- hello må inneholde mac-adr, bør egentlig kalle meldingen
  for JOIN, siden man liksom joiner network.

- on join, legg til flow for å forwarde til leder,
  dvs når vi får klient-meld inn, da betyr det vi ikke
  har flow så da installerer vi en flow for å forwarde
  til leder automatisk, så kan vi ha en lav idle timeout

- når leder får klient-msg så sender den ut aksept

- mininet er Omega_c og sender trust til S1, denne
  sender da ut meldinger som setter den som leder

  S2 og S3 at den er leder (her skal vi kjøre
