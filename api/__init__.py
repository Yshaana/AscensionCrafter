"""Service layer — the functions a FastAPI app will wrap 1:1 (ARCHITECTURE §2.7 rule 4).

Deliberately empty as of Phase 1 session 1a. It exists now, with a name, because the
decision it encodes ("a web API must call the identical function the CLI does") is
free today and a painful migration later. Modules land here as Phase 1 produces
things worth serving — `spell_profile()` (Task 7) is the first.

The layering, so it does not drift:

    cli/  ->  api/  ->  core/          never the reverse, and never cli/ -> core/
                                       directly once the api/ function exists
"""
