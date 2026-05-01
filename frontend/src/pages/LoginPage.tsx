import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.message || "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center text-white text-3xl mx-auto mb-4">
            🤖
          </div>
          <h1 className="text-2xl font-bold text-gray-900">SmartCS</h1>
          <p className="text-gray-600 mt-2">智能客服管理系统</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-3 rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                登录中...
              </span>
            ) : (
              "登录"
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t">
          <p className="text-sm text-gray-600 text-center mb-4">测试账号</p>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => {
                setUsername("admin");
                setPassword("admin123");
              }}
              className="px-3 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200 transition-colors"
            >
              <div className="font-medium">管理员</div>
              <div className="text-xs text-gray-500">admin</div>
            </button>
            <button
              onClick={() => {
                setUsername("agent1");
                setPassword("agent123");
              }}
              className="px-3 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200 transition-colors"
            >
              <div className="font-medium">客服</div>
              <div className="text-xs text-gray-500">agent1</div>
            </button>
            <button
              onClick={() => {
                setUsername("viewer");
                setPassword("viewer123");
              }}
              className="px-3 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200 transition-colors"
            >
              <div className="font-medium">访客</div>
              <div className="text-xs text-gray-500">viewer</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
