# CloudMart Resource Tagging — Lab Summary

- **Total resources**: 72
- **Tagged resources**: 0
- **Untagged resources**: 0 (0.00%)
- **Total monthly cost**: $0.00
- **Untagged monthly cost**: $0.00 (0.00% of total)

## Departments with highest untagged cost

- (Department column not present or no untagged resources)

## Most frequently missing tag fields
- No tag fields detected in dataset.

## Recommendations

1. Enforce required tags at provisioning time (use guardrails in IaC and cloud policies).
2. Implement a weekly tag compliance report and chargeback/showback for untagged costs.
3. Automate remediation for easy cases (fill with 'REMEDIATED' or owner-team mapping) and alert owners for manual fixes.
4. Use a centralized tagging taxonomy and require tags in CI/CD pipelines (Terraform/CloudFormation/Jenkins).

## Deliverables created

- `untagged_resources.csv` — list of untagged resources.
- `remediated_resources.csv` — simulated remediated dataset (untagged -> remediated).

----
Generated automatically from the uploaded `cloudmart_multi_account.csv`.