#! /usr/bin/env python
# encoding: utf-8


class ContextMsgResolver(object):
    def __init__(self, resolver, ctx, dependency):
        """Construct an instance.

        :param resolver: The resolver used to fetch the dependency
        :param ctx: A Waf Context instance.
        :param dependency: A Dependency instance.
        """
        self.resolver = resolver
        self.ctx = ctx
        self.dependency = dependency

    def resolve(self):
        """Print the resolved path to the terminal using Waf's Context.

        The print will format the start message differently depending on the
        "resolver_chain" and "resolver_action" attributes of the dependency
        object.

        Finally the path will be printed different depending on the
        "is_symlink" and "real_path" dependency object attributes.

        See a description of these attributes in the Depencency object docs.

        If the path is a symbolic link we print both the symbolic link and
        actual path on the file-system.

        :return: The path as a string.
        """

        start_msg = f'{self.dependency.resolver_chain} "{self.dependency.name}"'
        if self.dependency.resolver_action:
            start_msg += f" ({self.dependency.resolver_action})"
        self.ctx.start_msg(start_msg)

        path = self.resolver.resolve()

        if not path:
            # If a dependency is unavailable, we just
            # print the status message and continue
            # If this was an error we would have thrown
            # an exception
            self.ctx.end_msg("Unavailable", color="RED")
        else:
            if self.dependency.is_symlink:
                # We print the symlink path as a relative path if it is
                # inside the project folder
                symlink_path = path
                symlink_node = self.ctx.root.find_node(str(path))

                if symlink_node.is_child_of(self.ctx.srcnode):
                    symlink_path = symlink_node.path_from(self.ctx.srcnode)
                real_path = self.dependency.real_path
                detail = f"{symlink_path} => {real_path}"
            else:
                detail = path

            if self.dependency.resolver_info is not None:
                info = self.dependency.resolver_info
                # limit or extend info to 10 chars
                # if above replace the last 3 chars with "..."
                if len(info) > 10:
                    info = info[:7] + "..."
                else:
                    info = info.ljust(10)

                self.ctx.end_msg(f"{info} ({detail})")
            else:
                self.ctx.end_msg(f"{detail}")
        return path
