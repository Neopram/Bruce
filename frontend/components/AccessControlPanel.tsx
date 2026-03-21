import React, { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type Role = "admin" | "trader" | "viewer" | "api_bot";

interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  lastActive: string;
  status: "active" | "suspended" | "pending";
}

const PERMISSIONS = ["view_dashboard", "execute_trades", "manage_agents", "view_logs", "admin_settings", "api_access"] as const;
type Permission = typeof PERMISSIONS[number];

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  admin: [...PERMISSIONS],
  trader: ["view_dashboard", "execute_trades", "view_logs", "api_access"],
  viewer: ["view_dashboard", "view_logs"],
  api_bot: ["api_access", "view_dashboard"],
};

const ROLE_COLORS: Record<Role, string> = {
  admin: "bg-red-900 text-red-300",
  trader: "bg-blue-900 text-blue-300",
  viewer: "bg-gray-700 text-gray-300",
  api_bot: "bg-green-900 text-green-300",
};

export default function AccessControlPanel() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/users`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setUsers(data.users || data || []);
    } catch {
      setUsers([
        { id: "u1", name: "Admin User", email: "admin@bruce.ai", role: "admin", lastActive: "2024-03-15 17:30", status: "active" },
        { id: "u2", name: "Trader Bot", email: "bot@bruce.ai", role: "trader", lastActive: "2024-03-15 17:25", status: "active" },
        { id: "u3", name: "Viewer Account", email: "viewer@bruce.ai", role: "viewer", lastActive: "2024-03-14 09:00", status: "active" },
        { id: "u4", name: "API Service", email: "api@bruce.ai", role: "api_bot", lastActive: "2024-03-15 17:29", status: "active" },
        { id: "u5", name: "New User", email: "new@bruce.ai", role: "viewer", lastActive: "-", status: "pending" },
      ]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const changeRole = (userId: string, role: Role) => {
    setUsers((prev) => prev.map((u) => u.id === userId ? { ...u, role } : u));
  };

  const STATUS_COLORS: Record<string, string> = {
    active: "text-green-400",
    suspended: "text-red-400",
    pending: "text-yellow-400",
  };

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 animate-pulse space-y-3">
        <div className="h-4 bg-gray-700 rounded w-1/3" />
        {[1, 2, 3].map((i) => <div key={i} className="h-12 bg-gray-800 rounded" />)}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-5">
      <h2 className="text-lg font-bold text-amber-300">Access Control (RBAC)</h2>

      {/* User List */}
      <div className="space-y-2">
        {users.map((user) => (
          <div
            key={user.id}
            onClick={() => setSelectedUser(selectedUser === user.id ? null : user.id)}
            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedUser === user.id ? "border-amber-600 bg-amber-900/10" : "border-gray-700 bg-gray-800 hover:bg-gray-750"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-200">{user.name}</span>
                <span className="text-xs text-gray-500 ml-2">{user.email}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${ROLE_COLORS[user.role]}`}>{user.role.toUpperCase()}</span>
                <span className={`text-[10px] ${STATUS_COLORS[user.status]}`}>{user.status}</span>
              </div>
            </div>
            <div className="text-[10px] text-gray-600 mt-1">Last active: {user.lastActive}</div>

            {selectedUser === user.id && (
              <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
                {/* Role Assignment */}
                <div>
                  <span className="text-xs text-gray-400 block mb-1">Assign Role</span>
                  <div className="flex gap-1">
                    {(["admin", "trader", "viewer", "api_bot"] as Role[]).map((role) => (
                      <button
                        key={role}
                        onClick={(e) => { e.stopPropagation(); changeRole(user.id, role); }}
                        className={`text-[10px] px-2 py-1 rounded transition-colors ${
                          user.role === role ? ROLE_COLORS[role] : "bg-gray-700 text-gray-400 hover:bg-gray-600"
                        }`}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Permissions */}
                <div>
                  <span className="text-xs text-gray-400 block mb-1">Permissions</span>
                  <div className="grid grid-cols-2 gap-1">
                    {PERMISSIONS.map((perm) => {
                      const has = ROLE_PERMISSIONS[user.role].includes(perm);
                      return (
                        <div key={perm} className="flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${has ? "bg-green-500" : "bg-gray-600"}`} />
                          <span className={`text-[10px] ${has ? "text-gray-300" : "text-gray-600"}`}>{perm.replace(/_/g, " ")}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
