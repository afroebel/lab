#Based on AR_NotRecommended... It might be an improvement to try with data streaming...


import atsapi as ats
import time

board = ats.Board(systemId = 1, boardId = 1)
       
while True:
    board.configureAuxIO(14, 0) #TTL OFF
    time.sleep(10)
    board.configureAuxIO(14, 1) #TTL ON
    time.sleep(10)
