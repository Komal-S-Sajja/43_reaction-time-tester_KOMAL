import pygame
from .round import Round

# Game Engine

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)


class GameEngine:
    def __init__(
        self,
        width,
        height,
        rounds_total=5,
        min_wait_ms=1000,
        max_wait_ms=3000,
    ):
        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []

        self.result_shown_at = None
        self.result_pause_ms = 800

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)

        self.game_over = False
        self.difficulty_selection = False
        self.finished = False

    def handle_event(self, event):
        if self.game_over:
            self._handle_results_input(event)
            return

        if self.difficulty_selection:
            self._handle_difficulty_input(event)
            return

        is_click = event.type == pygame.MOUSEBUTTONDOWN
        is_space = (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_SPACE
        )

        if (is_click or is_space) and self.round.state != "result":
            reaction_ms = self.round.register_input()

            if reaction_ms is not None:
                self.reaction_times.append(reaction_ms)

            self.result_shown_at = pygame.time.get_ticks()

    def _handle_results_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.game_over = False
                self.difficulty_selection = True
            elif event.key == pygame.K_RETURN:
                self.finished = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.game_over = False
            self.difficulty_selection = True

    def _handle_difficulty_input(self, event):
        difficulty = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                difficulty = "Easy"
            elif event.key == pygame.K_2:
                difficulty = "Medium"
            elif event.key == pygame.K_3:
                difficulty = "Hard"

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos

            if 100 <= x <= 500:
                if 100 <= y <= 160:
                    difficulty = "Easy"
                elif 170 <= y <= 230:
                    difficulty = "Medium"
                elif 240 <= y <= 300:
                    difficulty = "Hard"

        if difficulty is not None:
            self._start_new_game(difficulty)

    def _start_new_game(self, difficulty):
        difficulty_settings = {
            "Easy": {
                "rounds": 3,
                "min_wait": 1500,
                "max_wait": 3500,
            },
            "Medium": {
                "rounds": 5,
                "min_wait": 1000,
                "max_wait": 3000,
            },
            "Hard": {
                "rounds": 7,
                "min_wait": 500,
                "max_wait": 2000,
            },
        }

        settings = difficulty_settings[difficulty]

        self.rounds_total = settings["rounds"]
        self.min_wait_ms = settings["min_wait"]
        self.max_wait_ms = settings["max_wait"]

        self.reaction_times = []
        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms,
        )

        self.result_shown_at = None
        self.game_over = False
        self.difficulty_selection = False
        self.finished = False

    def handle_input(self):
        # Reserved for continuously-held-key input; every action here
        # is a discrete click/keypress, handled in handle_event.
        pass

    def update(self):
        if self.game_over or self.difficulty_selection:
            return

        self.round.update()

        if self.round.state == "result":
            now = pygame.time.get_ticks()

            if now - self.result_shown_at >= self.result_pause_ms:
                self._start_next_round()

    def _start_next_round(self):
        if len(self.reaction_times) >= self.rounds_total:
            self.game_over = True
            return

        self.round = Round(
            self.min_wait_ms,
            self.max_wait_ms,
        )

    def average_reaction_ms(self):
        if not self.reaction_times:
            return 0

        return round(
            sum(self.reaction_times) / len(self.reaction_times)
        )

    def render(self, screen):
        if self.game_over:
            self._render_results(screen)
            return

        if self.difficulty_selection:
            self._render_difficulty_selection(screen)
            return

        if self.round.state == "waiting":
            bg = GRAY
            message = "Wait for green..."
        elif self.round.state == "go":
            bg = GREEN
            message = "Click now!"
        else:
            bg = BLUE
            message = (
                "False start!"
                if self.round.false_start
                else f"{self.round.reaction_ms} ms"
            )

        screen.fill(bg)

        text_surf = self.big_font.render(
            message,
            True,
            WHITE,
        )
        text_rect = text_surf.get_rect(
            center=(self.width // 2, self.height // 2)
        )
        screen.blit(text_surf, text_rect)

        round_num = min(
            len(self.reaction_times) + 1,
            self.rounds_total,
        )

        round_text = self.font.render(
            f"Round {round_num}/{self.rounds_total}",
            True,
            WHITE,
        )
        screen.blit(round_text, (10, 10))

        avg_text = self.font.render(
            f"Avg: {self.average_reaction_ms()} ms",
            True,
            WHITE,
        )
        screen.blit(
            avg_text,
            (self.width - 190, 10),
        )

    def _render_results(self, screen):
        screen.fill(BLUE)

        title = self.big_font.render(
            "Game Over!",
            True,
            WHITE,
        )
        title_rect = title.get_rect(
            center=(self.width // 2, 45)
        )
        screen.blit(title, title_rect)

        y = 90

        for index, reaction_ms in enumerate(
            self.reaction_times,
            start=1,
        ):
            reaction_text = self.font.render(
                f"Round {index}: {reaction_ms} ms",
                True,
                WHITE,
            )
            screen.blit(reaction_text, (100, y))
            y += 35

        average_text = self.font.render(
            f"Average: {self.average_reaction_ms()} ms",
            True,
            WHITE,
        )
        average_rect = average_text.get_rect(
            center=(self.width // 2, 290)
        )
        screen.blit(average_text, average_rect)

        play_again_text = self.font.render(
            "Space / Click: Play Again",
            True,
            WHITE,
        )
        play_again_rect = play_again_text.get_rect(
            center=(self.width // 2, 335)
        )
        screen.blit(play_again_text, play_again_rect)

        exit_text = self.font.render(
            "Enter: Exit",
            True,
            WHITE,
        )
        exit_rect = exit_text.get_rect(
            center=(self.width // 2, 375)
        )
        screen.blit(exit_text, exit_rect)

    def _render_difficulty_selection(self, screen):
        screen.fill(BLUE)

        title = self.big_font.render(
            "Choose Difficulty",
            True,
            WHITE,
        )
        title_rect = title.get_rect(
            center=(self.width // 2, 55)
        )
        screen.blit(title, title_rect)

        difficulties = [
            ("1 - Easy", "1500-3500 ms wait, 3 rounds"),
            ("2 - Medium", "1000-3000 ms wait, 5 rounds"),
            ("3 - Hard", "500-2000 ms wait, 7 rounds"),
        ]

        y = 120

        for name, description in difficulties:
            name_text = self.font.render(
                name,
                True,
                WHITE,
            )
            name_rect = name_text.get_rect(
                center=(self.width // 2, y)
            )
            screen.blit(name_text, name_rect)

            description_text = pygame.font.SysFont(
                "Arial",
                20,
            ).render(
                description,
                True,
                WHITE,
            )
            description_rect = description_text.get_rect(
                center=(self.width // 2, y + 30)
            )
            screen.blit(description_text, description_rect)

            y += 70

        instruction = pygame.font.SysFont(
            "Arial",
            20,
        ).render(
            "Press 1, 2, or 3 to choose",
            True,
            WHITE,
        )
        instruction_rect = instruction.get_rect(
            center=(self.width // 2, 350)
        )
        screen.blit(instruction, instruction_rect)
