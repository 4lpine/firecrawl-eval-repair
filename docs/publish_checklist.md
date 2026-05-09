# Publish Checklist

Create a public GitHub repository named:

```text
firecrawl-eval-repair
```

Recommended settings:

- owner: `4lpine`
- visibility: public
- initialize with README: no
- add `.gitignore`: no
- add license: optional

Then push from this directory:

```powershell
git remote -v
git push -u origin main
```

The remote is already configured as:

```text
https://github.com/4lpine/firecrawl-eval-repair.git
```

Before emailing Firecrawl, make sure the repository is public and that
`docs/live_eval_summary.md` renders correctly on GitHub.
