export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const repo = process.env.GITHUB_REPO; // e.g. "yourname/yourrepo"
  const token = process.env.GITHUB_TOKEN;

  try {
    const response = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
      method: "POST",
      headers: {
        "Accept": "application/vnd.github+json",
        "Authorization": `token ${token}`,
      },
      body: JSON.stringify({ event_type: "notion_trigger" }),
    });

    if (!response.ok) {
      const text = await response.text();
      return res.status(response.status).json({ error: text });
    }

    res.status(200).json({ success: true, message: "Workflow triggered!" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
