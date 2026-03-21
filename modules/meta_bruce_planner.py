"""
Meta-level strategic planning module.
Handles long-term goals, milestone tracking, resource allocation,
and coordination with strategic agents.
"""
import datetime
import json


def _safe_log_vector(category, message):
    """Safe wrapper for vector logging that handles import failures."""
    try:
        from modules.vector_logger import log_vector
        log_vector(category, message)
    except ImportError:
        pass


def _safe_store_task(goal, plan):
    """Safe wrapper for task storage that handles import failures."""
    try:
        from modules.task_memory import store_task
        store_task(goal, plan)
    except ImportError:
        pass


class MetaBrucePlanner:
    """High-level strategic planner for long-term autonomous objectives."""

    def __init__(self):
        self.objectives = []
        self.current_plan = {}
        self.milestones = {}
        self.resource_pool = {
            "compute": 100.0,
            "memory": 100.0,
            "network": 100.0,
            "api_calls": 1000,
        }
        self.resource_allocations = {}

    def define_objective(self, goal, timeline_days, priority=5):
        """Define a new strategic objective with timeline and priority."""
        entry = {
            "goal": goal,
            "defined_at": datetime.datetime.utcnow().isoformat(),
            "timeline_days": timeline_days,
            "priority": priority,
            "status": "active",
            "progress_pct": 0,
            "deadline": (
                datetime.datetime.utcnow() + datetime.timedelta(days=timeline_days)
            ).isoformat(),
        }
        self.objectives.append(entry)
        self._plan_for(goal)
        self._create_milestones(goal, timeline_days)
        return entry

    def _plan_for(self, goal):
        """Generate a strategic plan for a goal."""
        plan = {
            "goal": goal,
            "steps": [
                f"Break down '{goal}' into atomic tasks.",
                "Assign priority scores.",
                "Store in strategic memory.",
                "Initiate coordination with strategic agents.",
                "Monitor progress and adjust.",
            ],
            "status": "planned",
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        self.current_plan[goal] = plan
        _safe_store_task(goal, plan)
        _safe_log_vector("meta_bruce", f"Strategic plan created for: {goal}")

    def _create_milestones(self, goal, timeline_days):
        """Create milestone checkpoints for a goal."""
        milestone_count = max(2, min(10, timeline_days // 7))
        interval = timeline_days / milestone_count
        milestones = []
        for i in range(milestone_count):
            day = int(interval * (i + 1))
            milestones.append({
                "id": f"{goal}_m{i+1}",
                "description": f"Milestone {i+1} for '{goal}'",
                "target_day": day,
                "target_date": (
                    datetime.datetime.utcnow() + datetime.timedelta(days=day)
                ).isoformat(),
                "status": "pending",
                "expected_progress_pct": round((i + 1) / milestone_count * 100, 1),
            })
        self.milestones[goal] = milestones
        return milestones

    def update_milestone(self, goal, milestone_id, status="completed"):
        """Update the status of a milestone."""
        if goal not in self.milestones:
            return {"status": "error", "message": f"No milestones for goal: {goal}"}

        for ms in self.milestones[goal]:
            if ms["id"] == milestone_id:
                ms["status"] = status
                ms["updated_at"] = datetime.datetime.utcnow().isoformat()
                self._update_objective_progress(goal)
                return {"updated": milestone_id, "status": status}
        return {"status": "error", "message": f"Milestone not found: {milestone_id}"}

    def _update_objective_progress(self, goal):
        """Recalculate objective progress based on milestones."""
        if goal not in self.milestones:
            return
        total = len(self.milestones[goal])
        completed = sum(1 for ms in self.milestones[goal] if ms["status"] == "completed")
        progress = round(completed / total * 100, 1) if total else 0

        for obj in self.objectives:
            if obj["goal"] == goal:
                obj["progress_pct"] = progress
                if progress >= 100:
                    obj["status"] = "completed"
                break

    def allocate_resources(self, goal, compute=0, memory=0, network=0, api_calls=0):
        """Allocate resources from the pool to a goal."""
        request = {"compute": compute, "memory": memory, "network": network, "api_calls": api_calls}
        for resource, amount in request.items():
            if amount > self.resource_pool.get(resource, 0):
                return {"status": "error", "message": f"Insufficient {resource}"}

        for resource, amount in request.items():
            if amount > 0:
                self.resource_pool[resource] -= amount

        self.resource_allocations[goal] = self.resource_allocations.get(goal, {})
        for resource, amount in request.items():
            self.resource_allocations[goal][resource] = (
                self.resource_allocations[goal].get(resource, 0) + amount
            )
        return {"allocated": request, "remaining_pool": self.resource_pool}

    def release_resources(self, goal):
        """Release all resources allocated to a goal back to the pool."""
        if goal not in self.resource_allocations:
            return {"status": "error", "message": "No allocations for this goal"}

        released = self.resource_allocations.pop(goal)
        for resource, amount in released.items():
            self.resource_pool[resource] = self.resource_pool.get(resource, 0) + amount
        return {"released": released, "pool": self.resource_pool}

    def get_all_plans(self):
        """Return all current strategic plans."""
        return self.current_plan

    def get_objectives(self, status=None):
        """Return objectives, optionally filtered by status."""
        if status:
            return [o for o in self.objectives if o["status"] == status]
        return self.objectives

    def get_milestones(self, goal):
        """Return milestones for a specific goal."""
        return self.milestones.get(goal, [])

    def get_status(self):
        """Return planner status overview."""
        active = sum(1 for o in self.objectives if o["status"] == "active")
        completed = sum(1 for o in self.objectives if o["status"] == "completed")
        return {
            "total_objectives": len(self.objectives),
            "active": active,
            "completed": completed,
            "plans": len(self.current_plan),
            "resource_pool": self.resource_pool,
            "resource_allocations": self.resource_allocations,
        }
