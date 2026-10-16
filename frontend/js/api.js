// Central API wrapper with JSON error handling, CSRF token header and credentials
const API = {
  csrfToken: null,

  async request(endpoint, options = {}) {
    const defaultHeaders = {
      "Content-Type": "application/json"
    };

    if (this.csrfToken) {
      defaultHeaders["X-CSRF-Token"] = this.csrfToken;
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    if (options.body && typeof options.body !== "string") {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(endpoint, config);

      // Extract CSRF token header if provided by server
      const tokenHeader = response.headers.get("X-CSRF-Token");
      if (tokenHeader) {
        this.csrfToken = tokenHeader;
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = data && data.error ? data.error : `HTTP ${response.status} Error`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`[API] Request to ${endpoint} failed:`, err.message);
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, body) {
    return this.request(endpoint, { method: "POST", body });
  },

  put(endpoint, body) {
    return this.request(endpoint, { method: "PUT", body });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
};
