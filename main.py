from pyautogui import *
from multiprocessing import Process, Queue
import itertools
import pyautogui
import pydirectinput
import time
import threading
import keyboard

# some functions from pyautogui aren't working with applications like metin
# as replacement im using pydirectinput which is compatible with DirectX apps

catchTasks = []
throwTasks = []
lock = threading.Lock()


class Window:
    # when blocked program is not searching through this window
    blocked = False

    def __init__(self, id, position, region) -> None:
        self.id = id
        self.position = position
        self.region = region

    # waits minimal time between caught fish and new fish event
    def blockFishing(self) -> None:
        self.blocked = True
        time.sleep(7)
        self.blocked = False

    # clicks certain number of timer to catch fish
    def catchFish(self, number) -> None:
        print(f"catching fish: {self.position }")
        with lock:
            pyautogui.moveTo(self.position)
            pyautogui.click(button="right")
            for i in range(number):
                time.sleep(0.05)
                pydirectinput.press('space')

        # waits cooldown between catch and throw
        time.sleep(6.5)
        throwTasks.append(self.id)

    def throwBait(self) -> None:
        print(f"throwing bait {self.position}")
        with lock:
            pyautogui.moveTo(self.position)
            pyautogui.click(button="right")
            pydirectinput.press('1')
            time.sleep(0.01)
            pydirectinput.press('space')


def distinctValues(generator):
    result = [next(generator)]
    generator = itertools.chain([result[0]], generator)
    for i in generator:
        if abs(i[0] - result[-1][0] + i[1] - result[-1][1]) > 50:
            result.append(i)

    return result


def findWindows():
    windows = []
    matchingWindows = pyautogui.locateAllOnScreen(
        'images/map_icon.png', confidence=0.9)
    filteredWindows = distinctValues(matchingWindows)
    print(f"Znalezione okna: {filteredWindows}")

    id = 0
    for left, top, right, height in filteredWindows:

        position = [left-400, top]
        region = (left-420, top+30, 100, 120)
        windows.append(Window(id, position, region))
        id += 1

    return windows


def searchFishEvent(windows, images, q) -> None:

    while True:
        for window in windows:
            if window.blocked is False:
                for image in images:
                    lookForEvent = pyautogui.locateOnScreen(
                        image, confidence=0.7, grayscale=False, region=(window.region))
                    if lookForEvent is not None:
                        t1 = threading.Thread(
                            target=window.blockFishing, daemon=True)
                        t1.start()
                        q.put([window.id, images.index(image)+1])


def queueHandler(q):
    while True:
        if not q.empty():
            catchTasks.append(q.get())
        else:
            time.sleep(0.05)


def main():
    images = ["images/1.png", "images/2.png",
              "images/3.png", "images/4.png", "images/5.png"]

    # returns all clients active on screen
    # with map closed
    windows = findWindows()

    # Run process that search for image of number to click
    q = Queue()
    p = Process(target=searchFishEvent, args=(
        windows, images, q,), daemon=True)
    p.start()

    # Takes
    t = threading.Thread(target=queueHandler, args=(q,), daemon=True)
    t.start()

    # Program works till q is not pressed
    while not keyboard.is_pressed('q'):
        # priority on catching fish
        if len(catchTasks) >= 1:
            catch = catchTasks[0]
            catchTasks.pop()
            t = threading.Thread(
                target=windows[catch[0]].catchFish, args=(catch[1],), daemon=True)
            t.start()

        # if there is nothing to catch throw bait
        elif len(throwTasks) >= 1:
            throw = throwTasks[0]
            throwTasks.pop()
            windows[throw].throwBait()
        else:
            time.sleep(0.1)


if __name__ == '__main__':
    time.sleep(5)
    main()
