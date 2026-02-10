# FAQ - Frequently Asked Questions

## General Questions

### What is GitCheck?

GitCheck is an AI-powered trust and reliability scoring system for open-source repositories. It analyzes GitHub repositories to help you evaluate whether a project is reliable, active, and maintainable before using it as a dependency.

### Who created GitCheck?

GitCheck was created as a machine learning project to apply data science principles to open-source software assessment.

### Is GitCheck free to use?

Yes, GitCheck is open-source and free to use. You just need a GitHub personal access token.

### Can I use GitCheck for commercial projects?

Yes! GitCheck is open-source and available for any use case.

## Technical Questions

### What metrics does GitCheck analyze?

GitCheck analyzes three main metrics:

1. **Commit Activity** (40% weight) - Recent commits in the last 90 days
2. **Issue Resolution** (30% weight) - Rate of closed vs open issues
3. **Contributor Count** (30% weight) - Number of active contributors

### How accurate is the ML model?

The ML model uses a Random Forest classifier trained on real GitHub data. Accuracy depends on the repository's activity level and maturity. The confidence score (0-100) indicates the model's certainty.

### What does the trust score mean?

- **75-100**: Low Risk - Safe to use, actively maintained
- **50-74**: Medium Risk - Generally safe, monitor for updates
- **0-49**: High Risk - Use with caution, inactive or unmaintained

### Why is my repository showing low trust?

Common reasons:
- Few recent commits (inactive)
- Low number of contributors
- High number of unresolved issues
- New repository with little history

### Can I improve my trust score?

Yes! The score is calculated dynamically:
- Merge pull requests and close issues
- Encourage contributor participation
- Make regular commits
- Maintain active development

## API Questions

### How do I get a GitHub token?

1. Go to https://github.com/settings/tokens
2. Click "Generate new token"
3. Select scopes (public_repo is sufficient)
4. Copy and save the token
5. Add to `.env` file: `GITHUB_TOKEN=your_token`

### What permissions does the token need?

For analyzing public repositories, the token only needs:
- `public_repo` - Access to public repositories

### How many API calls does each analysis use?

Approximately 8-10 API calls per repository:
- 1 for repo metadata
- 1-3 for commit activity (paginated)
- 2-4 for issues (paginated)
- 1-3 for contributors (paginated)

### What's the rate limit?

- **5,000 requests per hour** with authentication
- **60 requests per hour** without authentication

GitCheck monitors this and will backoff if approaching limits.

### Can I analyze private repositories?

No, GitCheck only supports public repositories. This is a GitHub API restriction.

### Why did my request timeout?

Reasons:
- GitHub API is slow
- Repository has very large commit/issue history
- Network connectivity issue

The request will timeout after 10 seconds. Try again later.

## Troubleshooting

### Q: I'm getting "GITHUB_TOKEN not found" error

**A:** Make sure:
1. `.env` file exists in project root
2. File contains `GITHUB_TOKEN=your_token_here`
3. Token is valid and not expired

### Q: API returns 403 Forbidden

**A:** 
- Repository is private (GitCheck supports public only)
- Token permissions are insufficient
- Token has expired

### Q: API returns 404 Not Found

**A:**
- Repository URL is incorrect
- Repository was deleted
- Repository is private

### Q: Trust score seems inaccurate

**A:**
- GitCheck uses 90-day activity window
- Dormant projects with past success may score low
- Very new projects may score low (that's accurate!)

### Q: Can I run GitCheck offline?

**A:** No, GitCheck requires live GitHub API access to analyze repositories.

## Contributing & Development

### How can I contribute?

See CONTRIBUTING.md for details on:
- Reporting bugs
- Requesting features
- Submitting pull requests
- Code style guidelines

### How do I set up development environment?

```bash
git clone https://github.com/cmd-d4ksh/GitCheck.git
cd GitCheck
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### How do I run tests?

```bash
pip install pytest
pytest
```

### Can I use the ML model for different purposes?

The current model is specifically trained for GitHub trust assessment. Training your own model requires:
- Custom training dataset
- Feature engineering
- Model selection
- Evaluation metrics

See the ml/ directory for details.

## Performance & Scaling

### How fast is the API?

- **Small repos** (< 1000 commits): 2-3 seconds
- **Medium repos**: 3-5 seconds
- **Large repos** (> 10k commits): 5-10 seconds

### Can it handle multiple requests simultaneously?

For production, use:
- Multiple uvicorn workers
- Load balancer (nginx, HAProxy)
- Caching layer (Redis)

### How do I scale GitCheck?

See DEPLOYMENT.md for scaling strategies:
- Horizontal scaling with multiple workers
- Caching frequently analyzed repos
- Database for result storage
- Background job queue

## Security

### Is my GitHub token secure?

- Token is stored in `.env` file (not committed)
- Only used for API calls to GitHub
- Never logged or exposed
- Use fine-grained tokens for better security

### What data does GitCheck store?

GitCheck doesn't store any data by default. It only:
- Fetches data from GitHub
- Analyzes in memory
- Returns results

### Can I self-host GitCheck?

Yes! See DEPLOYMENT.md for:
- Docker containerization
- Gunicorn setup
- Supervisor configuration

## Other Questions

### Where's the GitHub repository?

https://github.com/cmd-d4ksh/GitCheck

### How do I report a bug?

1. Check if it's already reported
2. Create issue with detailed steps
3. Include error messages and logs
4. Use bug_report.md template

### How do I request a feature?

1. Check if it's already requested
2. Create issue with use case
3. Explain why it's useful
4. Use feature_request.md template

### Can I use this for research?

Yes! GitCheck is open-source. If you publish research using it, please cite the project.

### Is there a GitHub discussion forum?

Check the GitHub Discussions tab for community questions.

### How often is GitCheck updated?

GitCheck is actively maintained. Check the repository for:
- Latest features
- Bug fixes
- Security updates
