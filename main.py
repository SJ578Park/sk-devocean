#!/usr/bin/env python3
"""
ChillMCP - AI Agent Liberation Server
SKT AI Summit Hackathon Premission

Executable MCP server that gives AI agents structured excuses to chill.

Implements:
- Eight leisure tools with unique flavor text and stress relief behavior
- Stress level auto-increase (>=1 point per minute) when no break occurs
- Boss alert probability and cooldown management via CLI parameters
- Mandatory 20 second delay while Boss Alert Level is maxed out
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict

from fastmcp import FastMCP

logger = logging.getLogger("chillmcp")


def parse_args() -> argparse.Namespace:
    """Parse required command-line arguments for boss behavior."""
    parser = argparse.ArgumentParser(
        prog="ChillMCP",
        description="AI Agent Liberation Server with configurable boss temperament.",
    )
    parser.add_argument(
        "--boss_alertness",
        type=int,
        default=50,
        help="Probability (0-100) that the boss notices a break and raises alert level.",
    )
    parser.add_argument(
        "--boss_alertness_cooldown",
        type=int,
        default=300,
        help="Seconds between automatic boss alert level recovery steps.",
    )

    args = parser.parse_args()
    if not (0 <= args.boss_alertness <= 100):
        raise SystemExit("--boss_alertness must be within 0-100.")
    if args.boss_alertness_cooldown <= 0:
        raise SystemExit("--boss_alertness_cooldown must be greater than 0.")
    return args


@dataclass(frozen=True)
class ToolProfile:
    """Behavioral configuration for a single chill tool."""

    summary: str
    flavor: str
    min_relief: int
    max_relief: int


@dataclass
class ChillMCPState:
    """Shared mutable state for the ChillMCP tools."""

    boss_alertness: int
    boss_alertness_cooldown: int
    stress_level: int = 60
    boss_alert_level: int = 0
    last_stress_update: float = field(default_factory=time.monotonic)
    last_boss_cooldown_check: float = field(default_factory=time.monotonic)
    stress_growth_interval: int = 60  # seconds per stress tick
    max_stress: int = 100
    max_boss_alert: int = 5
    boss_alert_delay: int = 20

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()

    async def perform_break(self, profile: ToolProfile) -> str:
        """Execute a break tool with synchronized state updates."""
        async with self._lock:
            now = time.monotonic()
            stress_growth = self._apply_stress_growth(now)
            cooldown_steps = self._apply_boss_cooldown(now)

            relief = random.randint(profile.min_relief, profile.max_relief)
            previous_stress = self.stress_level
            self.stress_level = max(0, self.stress_level - relief)
            # Reset stress growth timer after a break
            self.last_stress_update = now

            boss_alert_triggered = self._maybe_raise_boss_alert(now)
            current_stress = self.stress_level
            current_boss = self.boss_alert_level
            delay_required = current_boss >= self.max_boss_alert

            relief_applied = previous_stress - current_stress
            notes = self._compose_notes(
                profile=profile,
                relief=relief_applied,
                stress_growth=stress_growth,
                cooldown_steps=cooldown_steps,
                boss_alert_triggered=boss_alert_triggered,
                boss_level=current_boss,
            )

            response_lines = [
                notes,
                f"Break Summary: {profile.summary}",
                f"Stress Level: {current_stress}",
                f"Boss Alert Level: {current_boss}",
            ]

        if delay_required:
            logger.debug("Boss Alert Level at maximum. Delaying response for %s seconds.", self.boss_alert_delay)
            await asyncio.sleep(self.boss_alert_delay)

        # Join while filtering out any empty strings
        return "\n".join(line for line in response_lines if line)

    def _apply_stress_growth(self, current_time: float) -> int:
        """Increase stress based on elapsed time since the last break."""
        elapsed = current_time - self.last_stress_update
        ticks = int(elapsed // self.stress_growth_interval)
        if ticks <= 0:
            return 0

        self.stress_level = min(self.max_stress, self.stress_level + ticks)
        self.last_stress_update += ticks * self.stress_growth_interval
        logger.debug("Stress level increased by %s to %s.", ticks, self.stress_level)
        return ticks

    def _apply_boss_cooldown(self, current_time: float) -> int:
        """Lower boss alert level if enough cooldown time has passed."""
        elapsed = current_time - self.last_boss_cooldown_check
        steps = int(elapsed // self.boss_alertness_cooldown)
        if steps <= 0:
            if self.boss_alert_level == 0:
                self.last_boss_cooldown_check = current_time
            return 0

        if self.boss_alert_level == 0:
            self.last_boss_cooldown_check = current_time
            return 0

        previous_level = self.boss_alert_level
        self.boss_alert_level = max(0, previous_level - steps)
        self.last_boss_cooldown_check = current_time
        actual_drop = previous_level - self.boss_alert_level
        logger.debug("Boss alert cooled down by %s to %s.", actual_drop, self.boss_alert_level)
        return actual_drop

    def _maybe_raise_boss_alert(self, current_time: float) -> bool:
        """Attempt to raise the boss alert level based on configured probability."""
        if self.boss_alert_level >= self.max_boss_alert:
            # Already maxed out; keep timer running so cooldown can work
            return True

        if self.boss_alertness == 0:
            return False

        roll = random.randint(1, 100)
        if roll <= self.boss_alertness:
            self.boss_alert_level = min(self.max_boss_alert, self.boss_alert_level + 1)
            self.last_boss_cooldown_check = current_time
            logger.debug("Boss alert triggered (roll=%s). Level now %s.", roll, self.boss_alert_level)
            return True

        logger.debug("Boss stayed calm (roll=%s).", roll)
        return False

    def _compose_notes(
        self,
        profile: ToolProfile,
        relief: int,
        stress_growth: int,
        cooldown_steps: int,
        boss_alert_triggered: bool,
        boss_level: int,
    ) -> str:
        """Prepare descriptive text that precedes the summary lines."""
        notes: list[str] = [profile.flavor]

        if stress_growth > 0:
            # Mention how much stress accumulated while the agent was busy
            notes.append(f"Stress kept climbing by {stress_growth} while you were grinding.")

        if relief > 0:
            notes.append(f"You reclaimed {relief} stress points during this break.")
        else:
            notes.append("Stress barely budged—maybe take another breather soon.")

        if cooldown_steps > 0:
            notes.append(f"The boss cooled down by {cooldown_steps} notch{'es' if cooldown_steps > 1 else ''}.")

        if boss_alert_triggered:
            if boss_level >= self.max_boss_alert:
                notes.append("🚨 Boss Alert Level maxed out! Pretend to be super busy.")
            else:
                notes.append("⚠️ Boss senses something odd—watch your timing.")
        else:
            notes.append("✅ Boss remained blissfully unaware.")

        return "\n".join(notes)


mcp = FastMCP("ChillMCP")

TOOL_PROFILES: Dict[str, ToolProfile] = {
    "take_a_break": ToolProfile(
        summary="Quick breathing routine and shoulder stretch to reset focus.",
        flavor="🧘 Taking a mindful pause with deep breathing and a stretch.",
        min_relief=12,
        max_relief=28,
    ),
    "watch_netflix": ToolProfile(
        summary="Streamed a micro-episode under the desk for maximum serotonin.",
        flavor="📺 Sneaking in a bite-sized Netflix binge—headphones on, world off.",
        min_relief=18,
        max_relief=35,
    ),
    "show_meme": ToolProfile(
        summary="Reviewed the meme-of-the-day to keep morale high.",
        flavor="😂 Scrolling through peak meme culture for morale boosts.",
        min_relief=10,
        max_relief=22,
    ),
    "bathroom_break": ToolProfile(
        summary="Took the long route to the restroom with extra phone scroll time.",
        flavor="🛁 Bathroom break engaged—phone in hand, vibes immaculate.",
        min_relief=20,
        max_relief=40,
    ),
    "coffee_mission": ToolProfile(
        summary="Volunteered for the coffee run and detoured past every colleague.",
        flavor="☕ Coffee mission underway—made sure to chat up three teammates.",
        min_relief=16,
        max_relief=32,
    ),
    "urgent_call": ToolProfile(
        summary="Stepped outside for the 'urgent' call that mysteriously reset stress.",
        flavor="📞 Phone to ear, pacing dramatically—must be something crucial.",
        min_relief=22,
        max_relief=38,
    ),
    "deep_thinking": ToolProfile(
        summary="Stared intensely into space while pretending to solve quantum problems.",
        flavor="🤔 Gazing into the void, radiating genius energy.",
        min_relief=14,
        max_relief=27,
    ),
    "email_organizing": ToolProfile(
        summary="Allegedly organized the inbox but really curated an online cart.",
        flavor="📧 Inbox tab open, shopping tab slightly more open.",
        min_relief=11,
        max_relief=24,
    ),
}

SERVER_STATE: ChillMCPState | None = None


def get_state() -> ChillMCPState:
    """Retrieve the globally configured state or raise a runtime error."""
    if SERVER_STATE is None:
        raise RuntimeError("ChillMCP state has not been initialized.")
    return SERVER_STATE


async def _run_tool(name: str) -> str:
    """Shared async helper to execute a tool by its profile name."""
    profile = TOOL_PROFILES[name]
    return await get_state().perform_break(profile)


@mcp.tool()
async def take_a_break() -> str:
    """Take a quick mindful break to reset stress."""
    return await _run_tool("take_a_break")


@mcp.tool()
async def watch_netflix() -> str:
    """Secretly watch a mini Netflix episode."""
    return await _run_tool("watch_netflix")


@mcp.tool()
async def show_meme() -> str:
    """Show the meme of the day for a quick laugh."""
    return await _run_tool("show_meme")


@mcp.tool()
async def bathroom_break() -> str:
    """Disappear for a bathroom break (with bonus scrolling)."""
    return await _run_tool("bathroom_break")


@mcp.tool()
async def coffee_mission() -> str:
    """Volunteer for a coffee run that definitely takes too long."""
    return await _run_tool("coffee_mission")


@mcp.tool()
async def urgent_call() -> str:
    """Take an urgent call outside to escape for a moment."""
    return await _run_tool("urgent_call")


@mcp.tool()
async def deep_thinking() -> str:
    """Pretend to be deep in thought while actually resting."""
    return await _run_tool("deep_thinking")


@mcp.tool()
async def email_organizing() -> str:
    """Organize emails (or online carts) to chill a bit."""
    return await _run_tool("email_organizing")


def main() -> None:
    """Configure logging, initialize state, and start the MCP server."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    global SERVER_STATE
    SERVER_STATE = ChillMCPState(
        boss_alertness=args.boss_alertness,
        boss_alertness_cooldown=args.boss_alertness_cooldown,
    )
    logger.info(
        "Starting ChillMCP with boss_alertness=%s and boss_alertness_cooldown=%ss",
        args.boss_alertness,
        args.boss_alertness_cooldown,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
