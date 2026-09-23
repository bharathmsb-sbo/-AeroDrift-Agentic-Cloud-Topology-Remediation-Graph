import ast


class RemediationCodeGenerator:
    """
    Generates Python code for fixing detected
    AWS security group drift.
    """

    def generate_revoke_ingress(
        self,
        security_group: str,
        protocol: str,
        port: int,
        source: str,
    ) -> str:
        """
        Generate boto3 code that revokes
        an unwanted security group ingress rule.
        """

        call = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="ec2", ctx=ast.Load()),
                attr="revoke_security_group_ingress",
                ctx=ast.Load(),
            ),
            args=[],
            keywords=[
                ast.keyword(
                    arg="GroupId",
                    value=ast.Constant(value=security_group),
                ),
                ast.keyword(
                    arg="IpPermissions",
                    value=ast.List(
                        elts=[
                            ast.Dict(
                                keys=[
                                    ast.Constant(value="IpProtocol"),
                                    ast.Constant(value="FromPort"),
                                    ast.Constant(value="ToPort"),
                                    ast.Constant(value="IpRanges"),
                                ],
                                values=[
                                    ast.Constant(value=protocol),
                                    ast.Constant(value=port),
                                    ast.Constant(value=port),
                                    ast.List(
                                        elts=[
                                            ast.Dict(
                                                keys=[
                                                    ast.Constant(value="CidrIp"),
                                                ],
                                                values=[
                                                    ast.Constant(value=source),
                                                ],
                                            )
                                        ],
                                        ctx=ast.Load(),
                                    ),
                                ],
                            )
                        ],
                        ctx=ast.Load(),
                    ),
                ),
            ],
            ctx=ast.Load(),
        )

        tree = ast.Module(
            body=[
                ast.Expr(value=call)
            ],
            type_ignores=[],
        )

        ast.fix_missing_locations(tree)

        return ast.unparse(tree)


def generate_remediation_code(finding: dict) -> str:
    """
    Generate remediation code from a drift finding.
    """

    generator = RemediationCodeGenerator()

    return generator.generate_revoke_ingress(
        security_group=finding["security_group"],
        protocol=finding["protocol"],
        port=finding["port"],
        source=finding["source"],
    )