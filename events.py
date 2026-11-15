"""
Minimal in-process pub/sub used to push real-time updates to every
connected browser tab over Server-Sent Events (SSE).

Design: a plain list of queue.Queue objects, one per connected client.
When something changes (a complaint is filed, updated, upvoted, or
deleted) app.py calls broadcast(), which drops a small JSON message onto
every subscriber's queue; each open /stream connection is just reading
from its own queue in a loop and forwarding whatever arrives to the
browser.

This lives entirely in one Python process's memory, which is exactly
right for the single Flask dev-server process this project runs on - no
extra infrastructure (Redis, a message broker, etc.) needed for a demo
or a viva. A production deployment spread across multiple worker
processes or machines would swap this module for a shared pub/sub
backend (e.g. Redis's PUBLISH/SUBSCRIBE) instead; nothing else in the
app - not the /stream route, not the broadcast() call sites - would
need to change, since they only depend on this file's two functions.
"""

import json
import queue
import threading

_subscribers = []
_lock = threading.Lock()


def subscribe():
    """Registers a new listener and returns its Queue. Call unsubscribe()
    with the same queue when the connection closes."""
    q = queue.Queue()
    with _lock:
        _subscribers.append(q)
    return q


def unsubscribe(q):
    with _lock:
        if q in _subscribers:
            _subscribers.remove(q)


def broadcast(event_type, **payload):
    """Push {"type": event_type, **payload} to every currently connected
    client. Never raises even if a subscriber's queue is somehow full or
    gone - a missed live update is a cosmetic issue (the next page load
    is always correct from the database), never a data-loss one."""
    message = json.dumps({"type": event_type, **payload}, default=str)
    with _lock:
        targets = list(_subscribers)
    for q in targets:
        try:
            q.put_nowait(message)
        except Exception:
            pass


def subscriber_count():
    with _lock:
        return len(_subscribers)
