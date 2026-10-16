// Authentication handler: login, registration, and logout flows

const Auth = {
  async checkSession() {
    try {
      const res = await API.get("/api/auth/me");
      return res.data;
    } catch {
      return null;
    }
  },

  async login(email, password) {
    const res = await API.post("/api/auth/login", { email, password });
    return res.data;
  },

  async register(formData) {
    const res = await API.post("/api/auth/register", formData);
    return res.data;
  },

  async logout() {
    try {
      await API.post("/api/auth/logout", {});
    } finally {
      window.location.href = "/pages/login.html";
    }
  }
};
