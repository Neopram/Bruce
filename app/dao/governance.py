# DAO Governance controller
import time
import uuid


class DAOGovernance:
    """Decentralized Autonomous Organization governance for proposals and voting."""

    def __init__(self):
        self._proposals = {}
        self._votes = {}  # proposal_id -> list of vote records

    def create_proposal(self, title, description, voting_period=86400):
        """Create a new governance proposal.

        Args:
            title: Proposal title.
            description: Detailed description of the proposal.
            voting_period: Duration in seconds for voting (default 24h).

        Returns:
            Dict with proposal details.
        """
        proposal_id = str(uuid.uuid4())[:8]
        now = time.time()

        proposal = {
            "proposal_id": proposal_id,
            "title": title,
            "description": description,
            "status": "active",
            "created_at": now,
            "voting_ends_at": now + voting_period,
            "voting_period": voting_period,
            "author": "system",
            "votes_for": 0,
            "votes_against": 0,
            "votes_abstain": 0,
            "total_voters": 0,
        }

        self._proposals[proposal_id] = proposal
        self._votes[proposal_id] = []
        return {"status": "created", "proposal_id": proposal_id, "title": title, "voting_ends_at": proposal["voting_ends_at"]}

    def vote(self, proposal_id, voter, vote_type, weight=1):
        """Cast a vote on a proposal.

        Args:
            proposal_id: The proposal to vote on.
            voter: Voter identifier (address or username).
            vote_type: 'for', 'against', or 'abstain'.
            weight: Voting weight/power (default 1).
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"error": f"Proposal '{proposal_id}' not found"}

        if proposal["status"] != "active":
            return {"error": f"Proposal is '{proposal['status']}', not active"}

        if time.time() > proposal["voting_ends_at"]:
            proposal["status"] = "closed"
            return {"error": "Voting period has ended"}

        # Check for duplicate votes
        existing = [v for v in self._votes[proposal_id] if v["voter"] == voter]
        if existing:
            return {"error": f"Voter '{voter}' has already voted on this proposal"}

        if vote_type not in ("for", "against", "abstain"):
            return {"error": "vote_type must be 'for', 'against', or 'abstain'"}

        vote_record = {
            "voter": voter,
            "vote_type": vote_type,
            "weight": weight,
            "timestamp": time.time(),
        }
        self._votes[proposal_id].append(vote_record)

        proposal[f"votes_{vote_type}"] += weight
        proposal["total_voters"] += 1

        return {"status": "voted", "proposal_id": proposal_id, "voter": voter, "vote_type": vote_type}

    def get_proposal(self, proposal_id):
        """Get detailed proposal status.

        Args:
            proposal_id: The proposal ID.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"error": f"Proposal '{proposal_id}' not found"}

        # Auto-close if voting period ended
        if proposal["status"] == "active" and time.time() > proposal["voting_ends_at"]:
            proposal["status"] = "closed"

        return dict(proposal)

    def get_results(self, proposal_id):
        """Get voting results for a proposal.

        Args:
            proposal_id: The proposal ID.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"error": f"Proposal '{proposal_id}' not found"}

        total_weight = proposal["votes_for"] + proposal["votes_against"] + proposal["votes_abstain"]
        quorum_met = total_weight >= 3  # Simple quorum: at least 3 weighted votes

        outcome = "pending"
        if proposal["status"] == "closed" or time.time() > proposal["voting_ends_at"]:
            if not quorum_met:
                outcome = "no_quorum"
            elif proposal["votes_for"] > proposal["votes_against"]:
                outcome = "approved"
            elif proposal["votes_against"] > proposal["votes_for"]:
                outcome = "rejected"
            else:
                outcome = "tied"

        return {
            "proposal_id": proposal_id,
            "title": proposal["title"],
            "votes_for": proposal["votes_for"],
            "votes_against": proposal["votes_against"],
            "votes_abstain": proposal["votes_abstain"],
            "total_voters": proposal["total_voters"],
            "total_weight": total_weight,
            "quorum_met": quorum_met,
            "outcome": outcome,
        }

    def list_proposals(self, status_filter=None):
        """List all proposals, optionally filtered by status.

        Args:
            status_filter: Optional 'active', 'closed', or None for all.
        """
        # Auto-close expired proposals
        now = time.time()
        for p in self._proposals.values():
            if p["status"] == "active" and now > p["voting_ends_at"]:
                p["status"] = "closed"

        proposals = []
        for p in self._proposals.values():
            if status_filter and p["status"] != status_filter:
                continue
            proposals.append({
                "proposal_id": p["proposal_id"],
                "title": p["title"],
                "status": p["status"],
                "votes_for": p["votes_for"],
                "votes_against": p["votes_against"],
                "total_voters": p["total_voters"],
                "created_at": p["created_at"],
            })
        return proposals
