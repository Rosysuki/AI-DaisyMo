# -*- coding: utf-8    -*-
# -*- file: DaisyMo.py -*-
# -*- CSDN: Daisy-Mo   -*-
# -*- GitHub: Rosysuki -*-
# -*- 贴吧: Daisy-Mo   -*-


__DEBUG__   = 0
BIRTH       = 8.10
DAISYMO     = 1
PLAYER      = 0
RANDOM_FACE = 0
DCOLOR      = (255, 155, 0)
QCOLOR      = (255, 255, 255)
BCOLOR      = (0, 0, 0)


def debug(err: str, txt: str) -> None:
    if __DEBUG__:
        print(f"@{err}: {txt}")


import os
import pygame
import requests
from pygame.locals import *
from cv2 import (
    VideoCapture,
    cvtColor,
    COLOR_RGB2BGR
)
from collections import (
    deque
)
from threading import (
    Thread
)
from sys import (
    platform,
    exit as sys_exit
)
from json import (
    dumps as json_dumps,
    loads as json_loads
)
from os import (
    path as os_path,
    listdir
)
from random import (
    choice,
    randint,
    seed
)
from base64 import (
    b64encode,
    b64decode
)
from time import (
    time,
    localtime,
    strftime
)
from typing import (
    NoReturn,
    Self,
    Tuple,
    Deque,
    Dict,
    List,
    Callable
)


os.environ["PYGAME_FREETYPE"] = '1'
os.environ["SDL_IME_SHOW_UI"] = '1'


class DaisyMo(object):

    first_meet: bool              = not os_path.exists("assets/key")

    base_url: str                 = r"https://api.deepseek.com/v1/chat/completions"

    model_name: str               = "deepseek-chat"

    api_key: str                  = None

    memory: List[Dict[str, str]]  = []

    offset: List[int]             = [0, 0]

    ratio: float                  = 0.72

    default_size: Tuple[int, int] = None

    last_face_path: str           = ''

    last_body_path: str           = ''

    photos: Deque[Tuple[pygame.SurfaceType, pygame.SurfaceType]] = deque([])

    text: str              = ''

    default_save_path: str = ''

    random_face_cache: List[str] = []

    random_body_cache: List[str] = []

    random_back_cache: List[str] = []

    def __init__(daisymo, ask_api_key: Callable[[], str]) -> NoReturn:
        if not DaisyMo.first_meet:
            with open("assets/key", 'r', encoding="utf-8") as api_key_file:
                DaisyMo.api_key = api_key_file.read().strip()

        else:
            DaisyMo.api_key = ask_api_key()

            if not __DEBUG__:
                with open("assets/key", 'w', encoding="utf-8") as api_key_file:
                    api_key_file.write(DaisyMo.api_key)


    def init(daisymo) -> Dict[str, str]:
        soul_file_path: str = "assets/DaisyMo.soul"

        if not os_path.exists(soul_file_path):
            debug("致命错误", "assets/DaisyMo.soul不存在！")
            sys_exit()

        daisymo_soul: str = ''
        with open(soul_file_path, 'r', encoding="utf-8") as daisymo_soul_file:
            daisymo_soul = daisymo_soul_file.read().strip()

        # if not __DEBUG__ and DaisyMo.first_meet:
        #     daisymo.save()

        if daisymo_soul[0] == '[':
            #daisymo.load(daisymo_soul)
            return daisymo.next(daisymo.last_chat(daisymo.parse(daisymo_soul)))

        seed(BIRTH)

        return daisymo.chat_then_parse(daisymo_soul)


    def update_offset_center(daisymo) -> Self:
        DaisyMo.offset[0] = (DaisyMo.default_size[0] - Screen.default_size[0]) // 2
        #DaisyMo.offset[1] = (DaisyMo.default_size[1] - Screen.default_size[1]) // 2

        return daisymo


    def update_default_size(daisymo, size: Tuple[int, int] = None) -> Self:
        if size is not None:
            DaisyMo.default_size = size
        
        elif DaisyMo.photos:
            DaisyMo.default_size = DaisyMo.photos[0][1].get_size()

        else:
            DaisyMo.default_size = (1405 * DaisyMo.ratio, 2500 * DaisyMo.ratio)
        
        return daisymo


    def chat(daisymo, text: str) -> str:
        DaisyMo.memory.append({"role": "user", "content": text})

        response: requests.Response = requests.post(
            DaisyMo.base_url,
            headers={"Authorization": "Bearer {}".format(b64decode(DaisyMo.api_key.encode()).decode())},
            json={"model": DaisyMo.model_name, "messages": DaisyMo.memory}
        )

        #print({"Authorization": "Bearer {}".format(DaisyMo.api_key)})
        #print({"model": DaisyMo.model_name, "message": DaisyMo.memory})

        if response.status_code != 200:
            debug("回复失败", f"返回码{response.status_code}")
            DaisyMo.memory.pop()
            return ''
                
        respond: str = response.json()["choices"][0]["message"]["content"].replace('```json', '').replace('```', '')
        DaisyMo.memory.append({"role": "assistant", "content": respond})

        if __DEBUG__:
            print('= ' * 10)
            print(respond)
            print('= ' * 10)

        return respond
    

    def chat_then_parse(daisymo, text: str) -> Dict[str, str]:
        if not text:
            debug("不能为空", "in chat_then_parse text")
            return {}

        respond_json: Dict[str, str] = {}
        raw: str = daisymo.chat(text)

        try:
            respond_json = json_loads(raw)

        except Exception as e:
            start = raw.find('{')
            end = raw.rfind('}') + 1

            if start == -1 or end == 0:
                return {}

            try:
                respond_json = json_loads(raw[start: end])
            except Exception as e:
                debug("解析失败", f"in chat_then_parse json_loads with error: {e}")
                return {}

        if not respond_json:
            debug("解释失败", "in chat_then_parse respond_json")
            return {}
        
        daisymo.next(respond_json)

        return respond_json
    

    def next(daisymo, respond_json: Dict[str, str]) -> Dict[str, str]:
        if DaisyMo.photos:
            last_face, last_body = DaisyMo.photos.pop()

        face_pic_path: str = "assets/daisymo/face/{}.png".format(respond_json.get("face", "温柔-说"))
        body_pic_path: str = "assets/daisymo/body/{}.png".format(respond_json.get("body", "便服单叉腰"))
        back_pic_path: str = "assets/bg/{}.jpg".format(respond_json.get("where", "学校门口白天"))

        face: pygame.SurfaceType = (
            pygame.image.load(face_pic_path).convert_alpha()
            if DaisyMo.last_face_path != face_pic_path
            else last_face
        )
        body: pygame.SurfaceType = (
            pygame.image.load(body_pic_path).convert_alpha()
            if DaisyMo.last_body_path != body_pic_path
            else last_body
        )
        back: pygame.SurfaceType = (
            pygame.image.load(back_pic_path).convert()
            if Screen.last_back_path != back_pic_path
            else Screen.default_back
        )

        if DaisyMo.ratio != 1.0:
            face = pygame.transform.rotozoom(face, 0.0, DaisyMo.ratio)
            body = pygame.transform.rotozoom(body, 0.0, DaisyMo.ratio)

        DaisyMo.photos.append((face, body))
        Screen.default_back = back
        DaisyMo.text = respond_json.get("text", "【回答失败！】")

        return respond_json
    

    def auto_save(daisymo) -> NoReturn:
        Thread(target=daisymo.save, name="daisymo_auto_save").start()


    def save(daisymo) -> bool:
        save_file_path: str = "assets/DaisyMo.soul"

        with open(save_file_path, 'w', encoding="utf-8") as save_file:
            save_file.write(json_dumps(DaisyMo.memory))

        return 1


    def load(daisymo, soul: str) -> Self:
        DaisyMo.memory = json_loads(soul)

        #DaisyMo.default_save_path = load_file_path

        return daisymo
    

    def parse(daisymo, content: str) -> Dict[str, str] | List[Dict[str, str]]:
        return json_loads(content)
    

    def random_face(daisymo) -> NoReturn:
        random_face_path: str = ''

        if not DaisyMo.random_face_cache:
            DaisyMo.random_face_cache.extend(
                [
                    "assets/daisymo/face/{}".format(e)
                    for e in listdir("assets/daisymo/face")
                ]
            )

        random_face_path = choice(DaisyMo.random_face_cache)

        if DaisyMo.photos:
            _, last_body = DaisyMo.photos.pop()

        face: pygame.SurfaceType = pygame.image.load(random_face_path).convert_alpha()

        if DaisyMo.ratio != 1.0:
            face = pygame.transform.rotozoom(face, 0.0, DaisyMo.ratio)

        DaisyMo.photos.append((face, last_body))


    def random_body(daisymo) -> NoReturn:
        random_body_path: str = ''

        if not DaisyMo.random_body_cache:
            DaisyMo.random_body_cache.extend(
                [
                    "assets/daisymo/body/{}".format(e)
                    for e in listdir("assets/daisymo/body")
                ]
            )

        random_body_path = choice(DaisyMo.random_body_cache)

        if DaisyMo.photos:
            last_face, _ = DaisyMo.photos.pop()

        body: pygame.SurfaceType = pygame.image.load(random_body_path).convert_alpha()

        if DaisyMo.ratio != 1.0:
            body = pygame.transform.rotozoom(body, 0.0, DaisyMo.ratio)

        DaisyMo.photos.append((last_face, body))


    def random_back(daisymo) -> NoReturn:
        random_back_path: str = ''

        if not DaisyMo.random_back_cache:
            DaisyMo.random_back_cache.extend(
                [
                    "assets/bg/{}".format(e)
                    for e in listdir("assets/bg")
                ]
            )

        random_back_path = choice(DaisyMo.random_back_cache)

        Screen.default_back = pygame.image.load(random_back_path).convert_alpha()
    

    def last_chat(daisymo, response: List[Dict[str, str]]) -> Dict[str, str]:
        DaisyMo.memory.extend(response)
        return daisymo.parse(response[-1].get("content", '{}'))
    

    def random_change_time(daisymo) -> float:
        random_time: float = randint(6, 12)

        debug("log", f"random_change_time -> {random_time}s")

        return random_time
    

    def history_surface(daisymo, size: Tuple[int, int]) -> pygame.SurfaceType:
        hsurf: pygame.SurfaceType = pygame.surface.Surface(size)
        hfont: pygame.font.FontType = pygame.font.Font("assets/font/SIMYOU.TTF", 16)
        x: int = 0
        y: int = 0
        target: str = ''
        current_text: pygame.SurfaceType = None
        content: Dict[str, str] = {}

        hsurf.fill(QCOLOR)

        current_text = hfont.render("<点击屏幕最顶上返回；长按屏幕中上则上翻；中下则下翻>", True, DCOLOR)
        hsurf.blit(current_text, (x, y))
        y += current_text.get_height() + 5

        for e in DaisyMo.memory[1: ]:
            if e["role"] == "user":
                target = "邱诚(我)"
                content = e["content"]

                current_text = hfont.render("{}: {}".format(target, content), True, BCOLOR)
            else:
                target = "墨小菊"
                content = daisymo.parse(e["content"])
            
                current_text = hfont.render(
                    "{}[{} {} {}]: {}".format(target, content["where"], content["body"], content["face"], content["text"]),
                    True,
                    BCOLOR
                )

            hsurf.blit(current_text, (x, y))
            y += current_text.get_height() + 5

        return hsurf


class Mixer(object):

    pointer: int = -1

    music_list: str = ["assets/bgm/bgm10_Ora.ogg"]

    def __init__(self) -> NoReturn:
        pygame.mixer.init()
        

    def air(self) -> NoReturn:
        Mixer.pointer = (Mixer.pointer + 1) % len(Mixer.music_list)

        pygame.mixer.music.load(Mixer.music_list[Mixer.pointer])
        pygame.mixer.music.play(-1)


    def exit(self) -> NoReturn:
        pygame.mixer.music.stop()


class Screen(object):

    default_size: Tuple[int, int]         = (1280, 720)

    default_back: pygame.SurfaceType      = None

    font: pygame.font.FontType            = None

    fast_text: pygame.SurfaceType         = None

    text_rect: Tuple[int, int]            = None

    player_input_text: pygame.SurfaceType = None

    player_input_rect: Tuple[int, int]    = None

    last_back_path: str                   = ''

    FPS: int                              = 20

    current_text: str                     = ''

    display_text: str                     = ''

    current_text_index: int               = 0

    fast_text_lines: List[pygame.SurfaceType] = []

    fast_text_rects: List[Tuple[pygame.SurfaceType, Tuple[int, int]]] = []

    player_input_lines: List[pygame.SurfaceType] = []

    player_input_rects: List[Tuple[pygame.SurfaceType, Tuple[int, int]]] = []

    typewriter_interval: float            = 0.03

    last_type_time: float                 = 0.0

    def __init__(self) -> NoReturn:
        not pygame.get_init() and pygame.init()

        if platform == "linux":
            self.screen = pygame.display.set_mode(self.default_size, FULLSCREEN | DOUBLEBUF)
            Screen.default_size = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode(Screen.default_size, vsync=1)
        
        pygame.display.set_caption("AI墨小菊")

        self.init()


    def init(self) -> NoReturn:
        Screen.font = pygame.font.Font("assets/font/SourceHanSansCN-Medium.otf", 28)
        Screen.dfont = pygame.font.Font("assets/font/SourceHanSansCN-Regular.otf", 18)
        Screen.qfont = pygame.font.Font("assets/font/SourceHanSansCN-Medium.otf", 18)
        self.main_botm: pygame.SurfaceType  = pygame.image.load("assets/ui/main_botm_demo.png").convert_alpha()
        self.main_botm_pos: Tuple[int, int] = (
            (self.screen.get_width() - self.main_botm.get_width()) // 2,
            self.screen.get_height() - self.main_botm.get_height()
        )

        # self.daisymo: DaisyMo = DaisyMo(self.ask_api_key)
        self.mixer: Mixer = Mixer()
        self.mixer.air()


    def title(self) -> Self:
        player: VideoCapture = VideoCapture("assets/ui/title_end_m.wmv")
        is_opened: bool = player.isOpened()
        clock: pygame.time.Clock = pygame.time.Clock()
        is_running: bool = True
        back: pygame.SurfaceType = pygame.image.load("assets/ui/title_end_m.jpg").convert()
        hint: pygame.SurfaceType = Screen.font.render("<点击任意处进入对话>", 1, DCOLOR)
        hint_alpha: int = 255
        hint_pos: Tuple[int, int] = (
            (self.screen.get_width() - hint.get_width()) // 2,
            (self.screen.get_height() - hint.get_height()) // 2 + 100
        )
        hint_forward: bool = False
        # white: pygame.SurfaceType = pygame.image.load("assets/ui/white.png").convert_alpha()
        # white_alpha: int = 0

        while is_opened:
            clock.tick(30)

            is_opened, frame = player.read()

            if not is_opened:
                break

            frame = pygame.surfarray.make_surface(cvtColor(frame, COLOR_RGB2BGR).swapaxes(0, 1))
            frame = pygame.transform.scale(frame, self.screen.get_size())

            self.screen.blit(frame, (0, 0))

            pygame.display.flip()


        pygame.event.clear()
        while is_running:
            
            for event in pygame.event.get():

                if event.type == MOUSEBUTTONDOWN or event.type == KEYDOWN:
                    is_running = False

            self.screen.blits(
                (
                    (back, (0, 0)),
                    (hint, hint_pos)
                )
            )
            pygame.display.flip()

            if not hint_forward:
                hint_alpha -= 0.66
                if hint_alpha <= 0:
                    hint_forward = not hint_forward
                    hint_alpha = 0
            
            else:
                hint_alpha += 0.66
                if hint_alpha >= 255:
                    hint_forward = not hint_forward
                    hint_alpha = 255

            hint.set_alpha(hint_alpha)

        # pygame.event.set_blocked([MOUSEMOTION])
        # while white_alpha < 255:
        #     # back.set_alpha(white_alpha := white_alpha + 0.8)
        #     # self.screen.blit(back, (0, 0))
        #     self.screen.fill([0, 0, 0, ])
        #     pygame.display.flip()

        self.daisymo: DaisyMo = DaisyMo(lambda : self.ask_api_key(back))

        pygame.event.clear()

        return self


    def wrap_text(self, text: str, max_width: int) -> List[str]:
        lines: List[str] = []
        current_line: str = ''

        for ch in text:
            test_line = current_line + ch
            if Screen.font.size(test_line)[0] > max_width and current_line:
                lines.append(current_line)
                current_line = ch
            else:
                current_line = test_line

        if current_line:
            lines.append(current_line)

        return lines


    def start_typewriter(self, text: str) -> NoReturn:
        self.current_text = text
        self.display_text = ''
        self.current_text_index = 0
        self.last_type_time = time()
        self.update_fast_text_rect()


    def step_typewriter(self) -> NoReturn:
        if self.current_text_index < len(self.current_text) and time() - self.last_type_time >= self.typewriter_interval:
            self.current_text_index += 1
            self.display_text = self.current_text[: self.current_text_index]
            self.last_type_time = time()
            self.update_fast_text_rect()


    def update(self) -> NoReturn:
        if Screen.default_back:
            self.screen.blit(Screen.default_back, (0, 0))

        if self.daisymo.photos:
            for each in DaisyMo.photos:
                self.screen.blits(
                    (
                        (each[1], DaisyMo.offset),
                        (each[0], DaisyMo.offset)
                    )
                )

        self.screen.blit(self.main_botm, self.main_botm_pos)

        for surf, rect in Screen.fast_text_rects:
            self.screen.blit(surf, rect)

        for surf, rect in Screen.player_input_rects:
            self.screen.blit(surf, rect)


    def unsafe_update(self) -> NoReturn: #deserted!
        self.screen.blits(
            (
                (Screen.default_back, (0, 0)),
                (DaisyMo.photos[0][1], DaisyMo.offset),
                (DaisyMo.photos[0][0], DaisyMo.offset),
                *Screen.fast_text_rects,
                *Screen.player_input_rects
            )
        )


    def update_fast_text_rect(self) -> NoReturn:
        text_to_render = self.display_text
        Screen.fast_text_lines = self.wrap_text(text_to_render, Screen.default_size[0] - 100)
        Screen.fast_text_rects = []

        base_y = (Screen.default_size[1] - len(Screen.fast_text_lines) * Screen.font.get_height()) - 100

        for index, line in enumerate(Screen.fast_text_lines):
            #surf = Screen.font.render(line, True, DCOLOR)
            surf = Screen.dfont.render(line, True, DCOLOR)
            rect = (
                (Screen.default_size[0] - surf.get_width()) // 2,
                base_y + index * Screen.font.get_height()
            )
            Screen.fast_text_rects.append((surf, rect))

        Screen.text_rect = Screen.fast_text_rects[0][1] if Screen.fast_text_rects else (0, 0)


    def update_player_input_rect(self, player_input: str) -> NoReturn:
        Screen.player_input_lines = []
        Screen.player_input_rects = []

        lines = self.wrap_text(player_input, Screen.default_size[0] - 100)
        base_y = Screen.default_size[1] - len(lines) * Screen.font.get_height() - 20
        x = Screen.text_rect[0]

        for index, line in enumerate(lines):
            #surf = Screen.font.render(line, True, QCOLOR)
            surf = Screen.qfont.render(line, True, QCOLOR)
            rect = (
                x,
                base_y + index * Screen.font.get_height()
            )
            Screen.player_input_rects.append((surf, rect))

        Screen.player_input_text = Screen.player_input_lines[0] if Screen.player_input_lines else None
        Screen.player_input_rect = Screen.player_input_rects[0][1] if Screen.player_input_rects else (x, base_y)


    def parse(self) -> NoReturn:
        self.start_typewriter(DaisyMo.text)
        self.update_player_input_rect('')


    def main(self) -> NoReturn:
        run: bool                 = True
        script: Dict[str, str]    = None
        player_input: str         = ''
        root: int                 = DAISYMO
        input_active: bool        = False
        clock: pygame.time.Clock  = pygame.time.Clock()
        # last_chat_time: float     = 0.0
        # random_change_time: float = 1000
        x = y = 0

        script = self.daisymo.init()
        self.daisymo.update_default_size().update_offset_center()
        self.parse()

        bug_normal: pygame.SurfaceType = pygame.image.load("assets/ui/title_btn_bug_normal.png").convert_alpha()
        bug_over: pygame.SurfaceType = pygame.image.load("assets/ui/title_btn_bug_over.png").convert_alpha()
        bug_rect: Tuple[4] = (
            0,
            self.screen.get_height() // 4,
            0 + bug_normal.get_width(),
            self.screen.get_height() // 4 + bug_normal.get_height()
        )
        hint: pygame.SurfaceType = pygame.image.load("assets/ui/YorN_botm_exit.bmp").convert()
        hint_pos: Tuple[2] = (
            (self.screen.get_width() - hint.get_width()) // 2,
            (self.screen.get_height() - hint.get_height()) // 2
        )

        history_normal: pygame.SurfaceType = pygame.image.load("assets/ui/main_btn_backlog_normal.png").convert_alpha()
        history_over: pygame.SurfaceType = pygame.image.load("assets/ui/main_btn_backlog_over.png").convert_alpha()
        history_rect: Tuple[4] = (
            0,
            self.screen.get_height() - history_normal.get_height(),
            (0, history_normal.get_width()),
            (self.screen.get_height() - history_normal.get_height(), self.screen.get_height())
        )

        other_font: pygame.font.FontType = pygame.font.Font("assets/font/SIMYOU.TTF", 15)
        other_font.set_underline(1)
        other_text: pygame.SurfaceType = other_font.render(
            "时间: {}".format(strftime("%Y年%m月%d日%H时%M分%S秒", localtime())),
            True,
            DCOLOR
        )
        other_pos: Tuple[2] = (
            hint_pos[0],
            self.screen.get_height() - other_text.get_height()
        )

        while run:

            other_text = other_font.render(
                "时间: {}".format(strftime("%Y年%m月%d日%H时%M分%S秒", localtime())),
                True,
                DCOLOR
            )

            clock.tick(Screen.FPS)
            self.step_typewriter()

            for event in pygame.event.get():

                if event.type == QUIT:
                    run = not run
                    break

                elif event.type == MOUSEBUTTONDOWN:
                    x, y = event.pos

                    if history_rect[2][0] <= x <= history_rect[2][1] and history_rect[3][0] <= y <= history_rect[3][1]:
                        self.history_menu()
                        break

                    if platform == "linux":
                        pygame.key.start_text_input()
                    input_active = True

                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        run = not run

                    elif event.key == K_RETURN:
                        debug("log", "key return for chat")
                        if platform == "linux":
                            pygame.key.stop_text_input()
                        input_active = False

                        self.daisymo.chat_then_parse(player_input)
                        self.start_typewriter(DaisyMo.text)
                        self.update_player_input_rect('')
                        player_input = ''
                        # last_chat_time = time()
                        # random_change_time = self.daisymo.random_change_time()
                        self.daisymo.auto_save()

                    elif event.key in (K_BACKSPACE, K_DELETE):
                        player_input = player_input[: -1]
                        self.update_player_input_rect(player_input)
                        debug("log", f"DELETE current player_input: {player_input}")

                    elif __DEBUG__ and event.key == K_s and not self.daisymo.save():
                        debug("保存失败", "save in K_s")

                    elif event.key == K_1:
                        self.daisymo.random_face()

                    elif event.key == K_2:
                        self.daisymo.random_body()

                    elif event.key == K_3:
                        self.daisymo.random_back()

                elif event.type == TEXTINPUT and input_active:
                    player_input += event.text
                    self.update_player_input_rect(player_input)
                    debug("log", f"TEXTINPUT current player_input: {player_input}")

                elif event.type == MOUSEMOTION:
                    x, y = event.pos

            # if RANDOM_FACE and  time() - last_chat_time >= random_change_time:
            #     debug("log", "random_change_time is over!")
            #     self.daisymo.random_face()
            #     last_chat_time = time()
            #     random_change_time = self.daisymo.random_change_time()

            #self.unsafe_update()
            self.update()

            if bug_rect[0] <= x <= bug_rect[2] and bug_rect[1] <= y <= bug_rect[3]:
                self.screen.blits(
                    (
                        (bug_over, bug_rect[: 2]),
                        (hint, hint_pos)
                    )
                )
            else:
                self.screen.blits(
                    (
                        (bug_normal, bug_rect[: 2]),
                        (other_text, other_pos)
                    )
                )

            if history_rect[2][0] <= x <= history_rect[2][1] and history_rect[3][0] <= y <= history_rect[3][1]:
                self.screen.blit(history_normal, history_rect[: 2])
            else:
                self.screen.blit(history_over, history_rect[: 2])

            pygame.display.flip()

        self.exit()


    def exit(self) -> NoReturn:
        self.daisymo.save()
        self.mixer.exit()
        pygame.quit()


    def ask_api_key(self, back: pygame.SurfaceType, title: str = "初次进入，需输入Api-Key") -> str:
        asking: bool = True
        inputing: bool = False
        api_key: str = ''

        Screen.font.set_bold(1)

        hint_text: pygame.SurfaceType = Screen.font.render(title, True, BCOLOR)
        hint_pos: List[int, int] = [
            (self.screen.get_width() - hint_text.get_width()) // 2,
            (self.screen.get_height() - hint_text.get_height()) // 3
        ]
        api_key_text: pygame.SurfaceType = Screen.font.render(api_key, True, DCOLOR)
        api_key_pos: List[int, int] = [
            (self.screen.get_width() - api_key_text.get_width()) // 2,
            (self.screen.get_height() - api_key_text.get_height()) // 2
        ]
        click_text: pygame.SurfaceType = Screen.font.render("<点击屏幕唤醒键盘>", True, DCOLOR)
        click_pos: Tuple[2] = (
            (self.screen.get_width() - click_text.get_width()) // 2,
            (self.screen.get_height() - click_text.get_height()) // 4
        )

        while asking:

            for event in pygame.event.get():

                if event.type == MOUSEBUTTONDOWN:
                    if platform == "linux":
                        pygame.key.start_text_input()
                    inputing = True

                elif event.type == TEXTINPUT and inputing:
                    api_key += event.text
                    api_key_text = Screen.font.render(api_key, True, DCOLOR)
                    api_key_pos[0] = (self.screen.get_width() - api_key_text.get_width()) // 2

                elif event.type == KEYDOWN:
                    if event.key in (K_DELETE, K_BACKSPACE):
                        api_key = api_key[: -1]
                        api_key_text = Screen.font.render(api_key, True, DCOLOR)
                        api_key_pos[0] = (self.screen.get_width() - api_key_text.get_width()) // 2

                    elif event.key == K_RETURN:
                        if platform == "linux":
                            pygame.key.stop_text_input()
                        inputing = asking = False

            self.screen.blits(
                (
                    (back, (0, 0)),
                    (hint_text, hint_pos),
                    (api_key_text, api_key_pos)
                )
            )

            if not inputing:
                self.screen.blit(click_text, click_pos)

            pygame.display.flip()

        Screen.font.set_bold(0)

        return b64encode(api_key.encode()).decode()
    

    def history_menu(self) -> NoReturn:
        screen_width, screen_height = self.screen.get_size()

        history_surf: pygame.SurfaceType = self.daisymo.history_surface((screen_width, screen_height))
        history_surf_pos: List[2] = [0, 0]
        history_board: pygame.SurfaceType = pygame.image.load("assets/ui/backlog_botm.png").convert_alpha()
        history_board_pos: Tuple[2] = (0, 0)

        last_x = last_y = 0

        running: bool = True
        rolling_up: bool = False
        rolling_down: bool = False
        while running:

            for event in pygame.event.get():

                if event.type == QUIT:
                    running = False

                elif event.type == MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if 0 <= x <= screen_width and 0 <= y <= screen_height // 8:
                        running = False
                    if 0 <= x <= screen_width and screen_height // 8 <= y <= screen_height // 2:
                        rolling_up = True
                    if 0 <= x <= screen_width and screen_height // 2 <= y <= screen_height:
                        rolling_down = True
                    # if 0 <= x <= screen_width // 2 and 0 <= y <= screen_height:
                    #     rolling_left = True
                    # if screen_width // 2 <= x <= screen_width and 0 <= y <= screen_height:
                    #     rolling_right = True

                elif event.type == MOUSEBUTTONUP:
                    rolling_down = rolling_up = rolling_left = rolling_right = False

            if rolling_down:
                history_surf_pos[1] -= 0.5
            if rolling_up:
                history_surf_pos[1] += 0.5
            # if rolling_left:
            #     history_surf_pos[0] -= 0.5
            # if rolling_right:
            #     history_surf_pos[0] += 0.5

            self.screen.fill(QCOLOR)
            self.screen.blit(history_surf, history_surf_pos)
            # self.screen.blits(
            #     (
            #         #(history_board, history_board_pos),
            #         (history_surf, history_surf_pos)
            #     )
            # )
            pygame.display.update()


if __name__ == "__main__":
    (
        Screen()
        .title()
        .main()
    )