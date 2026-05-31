# -*- coding: utf-8    -*-
# -*- file: DaisyMo.py -*-
# -*- CSDN: Daisy-Mo   -*-
# -*- GitHub: Rosysuki -*-

# 声明：
# 本项目为《三色绘恋》同人开源项目，侵权必删！
# 使用的资产（如立绘等）全部来自解包后的《三色绘恋》本体。
# 考虑到跨平台，本项目不采取分模块项目架构。
# 欢迎大家建言献策，为这个项目贡献代码和创意！如果你有任何想法或者建议，欢迎在GitHub上提交issue或者pull request。
# GitHub地址：
#

# 说明：
# 1.首先会弹出一个窗口让你选择一个文本文件，里面需要存储你的API-KEY，选好后点击打开。
# 2.接着会弹出另一个窗口让你选择一个soul文件，soul文件是之前保存的对话记录，选好后点击打开。
# 3.若这是你第一次使用，那么请选择根目录下的DaisyMo.soul文件，里面有一个初始设定，可以随意修改。
# 4.之后就会进入主界面，点击屏幕任意位置可以激活输入，输入完成后按回车提交，AI墨小菊就会根据你的输入进行回复。
# 5.在主界面，按下S键可以保存当前的对话记录，保存时会弹出一个窗口让你选择保存位置和文件名，保存后会得到一个soul文件，这个文件可以在下一次使用时加载，继续之前的对话。

__DEBUG__   = 1
BIRTH       = 8.10
DAISYMO     = 1
PLAYER      = 0
RANDOM_FACE = 0

def debug(err: str, txt: str) -> None:
    if __DEBUG__:
        print(f"@{err}: {txt}")


import os
import pygame
import requests
from pygame.locals import *
from tkinter.filedialog import (
    askopenfilename,
    asksaveasfilename
)
from collections import (
    deque
)
from sys import (
    platform,
    exit as sys_exit
)
from json import (
    dump as json_dump,
    load as json_load,
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
from time import (
    time
)
from typing import (
    NoReturn,
    Self,
    Tuple,
    Deque,
    Dict,
    List,
    Any
)


os.environ["PYGAME_FREETYPE"] = '1'
os.environ["SDL_IME_SHOW_UI"] = '1'


class DaisyMo(object):

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

    def __init__(daisymo) -> NoReturn:
        api_key_file_path: str = askopenfilename(title="请选择储存API-KEY的文件：")

        if not os_path.exists(api_key_file_path):
            debug("错误", "文件路径不存在！")
            sys_exit()

        with open(api_key_file_path, 'r', encoding="utf-8") as api_key_file:
            DaisyMo.api_key = api_key_file.read().strip()


    def init(daisymo) -> Dict[str, str]:
        soul_file_path: str = askopenfilename(title="请选择soul文件", defaultextension=".soul")

        if not os_path.exists(soul_file_path):
            debug("错误", "文件路径不存在！")
            sys_exit()

        daisymo_soul: str = ''
        with open(soul_file_path, 'r', encoding="utf-8") as daisymo_soul_file:
            daisymo_soul = daisymo_soul_file.read().strip()

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
            headers={"Authorization": "Bearer {}".format(DaisyMo.api_key)},
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
            print('=')
            print(respond)
            print('=')

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

        face_pic_path: str = r"assets\daisymo\face\{}.png".format(respond_json.get("face", "温柔-说"))
        body_pic_path: str = r"assets\daisymo\body\{}.png".format(respond_json.get("body", "便服单叉腰"))
        back_pic_path: str = r"assets\bg\{}.jpg".format(respond_json.get("where", "学校门口白天"))

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
        daisymo.save()


    def save(daisymo) -> bool:
        save_file_path: str = asksaveasfilename(defaultextension=".soul")
        if not save_file_path:
            debug("警告", "该路径不合规！")
            return 0

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
                    r"assets\daisymo\face\{}".format(e)
                    for e in listdir(r"assets\daisymo\face")
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
                    r"assets\daisymo\body\{}".format(e)
                    for e in listdir(r"assets\daisymo\body")
                ]
            )

        random_body_path = choice(DaisyMo.random_body_cache)

        if DaisyMo.photos:
            last_face, _ = DaisyMo.photos.pop()

        body: pygame.SurfaceType = pygame.image.load(random_body_path).convert_alpha()

        if DaisyMo.ratio != 1.0:
            body = pygame.transform.rotozoom(body, 0.0, DaisyMo.ratio)

        DaisyMo.photos.append((last_face, body))
    

    def last_chat(daisymo, response: List[Dict[str, str]]) -> Dict[str, str]:
        return daisymo.parse(response[-1].get("content", '{}'))
    

    def random_change_time(daisymo) -> float:
        random_time: float = randint(6, 12)

        debug("log", f"random_change_time -> {random_time}s")

        return random_time


class Screen(object):

    default_size: Tuple[int, int]         = (1280, 720)

    default_back: pygame.SurfaceType      = None

    font: pygame.font.FontType            = None

    fast_text: pygame.SurfaceType         = None

    text_rect: Tuple[int, int]            = None

    player_input_text: pygame.SurfaceType = None

    player_input_rect: Tuple[int, int]    = None

    last_back_path: str                   = ''

    FPS: int                              = 15

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
        self.daisymo: DaisyMo = DaisyMo()

        not pygame.get_init() and pygame.init()

        if platform == "linux":
            self.screen = pygame.display.set_mode(self.default_size, FULLSCREEN | DOUBLEBUF)
            Screen.default_size = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode(Screen.default_size, vsync=1)
        
        pygame.display.set_caption("AI墨小菊")

        self.init()


    def init(self) -> NoReturn:
        Screen.font = pygame.font.SysFont("幼圆", 26)


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
            self.display_text = self.current_text[:self.current_text_index]
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

        for surf, rect in Screen.fast_text_rects:
            self.screen.blit(surf, rect)

        for surf, rect in Screen.player_input_rects:
            self.screen.blit(surf, rect)


    def unsafe_update(self) -> NoReturn:
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

        base_y = (Screen.default_size[1] - len(Screen.fast_text_lines) * Screen.font.get_height()) // 4

        for index, line in enumerate(Screen.fast_text_lines):
            surf = Screen.font.render(line, True, (0, 0, 0))
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
            surf = Screen.font.render(line, True, (0, 0, 0))
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
        last_chat_time: float     = 0.0
        random_change_time: float = 1000

        script = self.daisymo.init()
        self.daisymo.update_default_size().update_offset_center()
        self.parse()

        while run:

            clock.tick(Screen.FPS)
            self.step_typewriter()

            for event in pygame.event.get():

                if event.type == QUIT:
                    run = not run
                    break

                elif event.type == MOUSEBUTTONDOWN:
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
                        last_chat_time = time()
                        random_change_time = self.daisymo.random_change_time()

                    elif event.key in (K_BACKSPACE, K_DELETE):
                        player_input = player_input[: -1]
                        self.update_player_input_rect(player_input)
                        debug("log", f"DELETE current player_input: {player_input}")

                    elif __DEBUG__ and event.key == K_s and not self.daisymo.save():
                        debug("保存失败", "save in K_s")

                elif event.type == TEXTINPUT and input_active:
                    player_input += event.text
                    self.update_player_input_rect(player_input)
                    debug("log", f"TEXTINPUT current player_input: {player_input}")

            if RANDOM_FACE and  time() - last_chat_time >= random_change_time:
                debug("log", "random_change_time is over!")
                self.daisymo.random_face()
                last_chat_time = time()
                random_change_time = self.daisymo.random_change_time()

            self.unsafe_update()
            pygame.display.flip()


if __name__ == "__main__":
    Screen().main()