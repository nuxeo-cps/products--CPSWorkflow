$Id$

==============
CPSWorkflow
==============

CPSWorkflow is a product defining extensions for DCWorkflow to implement a
CPS specific behavior

CPSWorkflow is 'stock' CMF and Plone compatible but if you may want to take
advantage of all advanced possiblities of CPSWorkflow you will need
CPSCore which contains an event service tool, a proxy system that can allows
you to have a publication mecanism and full 'workflow driven' CMS.

It adds the following elements :

 1) Placeful workflow configuration
 2) Workflow transition flags
 3) Stack workflows mecanism

1) Placeful workflow configuration

    In CPS workflows are placeful, this means that we can decide that
    for a given subtree, a given portal_type will follow a given
    workflow. A placeful (local) workflow is used for instance to have
    a subtree dedicated to public content where objects must pass
    through a reviewing process, and another subtree where the objects
    can be created and worked upon easily by the members.

    To create a placeful workflow configuration, a 'CPS Workflow
    Configuration' object must be created in the ZMI. It's then possible
    to define for each portal type what workflow it has to follow.

    When a workflow is configured in a folder, it applies to the folder
    itself and all its subobjects, recursively. Sometimes we want to
    configure a workflow for all the subobjects of a folder but not for
    the folder itself. This can be done using a "Below workflow chain".

2) Workflows

    The workflows are based on DCWorkflow with some extensions.

    Workflows control all the operations of a site, and all the security
    checks.

    A number of transition flags have been added to DCWorkflow. These
    flags govern some special CPS behaviors for the transition. They
    can be subdivided in several categories.

    Allowing subobject behavior

      A container has responsibility for globally allowing certain
      behaviors for its subobjects. This covers creation, deletion,
      moving into the container, copying into the container, publishing
      into the container, checkout into the container.

      Once a container allows certain operation, the workflow for the
      portal type itself will have to allow the operation too.

      Some of these behaviors are checked by the
      manage_CPScopyObjects, manage_CPScutObjects and
      manage_CPSpasteObjects methods. This will be integrated into
      core Zope methods later.

    Initial transitions

      An initial transition is a transition followed when an object is
      created (or published, checked out, etc.) in a container. It does
      not have an initial state, but the destination state is the one
      the object will have after creation. When asking for the creation
      of a portal type, only those that have a suitable initial
      transition will be allowed. The standard "initial state" of
      DCWorkflow is not used.

      "Transition for checkin" is logically grouped together with those.
      It's a transition an object will follow when it is on the
      receiving end of a checkin (i.e., when it is the reference object
      into which a modification is checked back in).

    Specific behavior

      - "Freeze object" is used by all transitions going to a state
        where the object should not be modified anymore.

      - "Publishing, with initial transitions" is used as a mechanism
        for publishing an object into another container.

      - "Checkout, with initial transitions" is used to checkout an
        object into another container.

      - "Checkin, with allowed transitions" is used to checkin an object
        back into its original version.

      - "Merge object with existing in same state" is used when in the
        destination state there should be only one docid in a state,
        e.g. only one published revision while several ones are
        pending.

  Publishing

    The term "Publishing" is used here to represent any kind of
    operation that involves taking a document in a workspace and
    requesting its publication in a section.

    In such an operation, two containers are used, which means two
    workflows. There is a source workflow for the document, that has to
    have a "publishing" operation, and in the destination container two
    conditions must be met: the destination container has to allow
    subobject publising (note that local roles of the source container
    have no meaning in the destination container), and the destination
    workflow for the portal type of the document has to have some
    initial transition for publishing, which will be used when the
    document is "published" or "submitted" in the section. The guards
    (conditions) on these initial transitions express who is authorized
    to do which initial transition, and can thus distinguish between a
    "submit" and a direct "publish".

    Note: a way to take into account the local roles of the source
    container will maybe have to be devised in the future.

    The 'doActionFor' call for a publishing transition takes 2
    arguments, 'dest_container' and 'initial_transition'. They describe
    the destination container into which the publishing must occur, and
    the initial transition to follow there. This initial transition will
    be validated against the allowed initial transitions specified in
    the workflow.

  Checkout and checkin

    Checkout and checkin are a way to take a document from a reference
    version, make modifications to it, and fold back the modifications
    into the original.

    The 'doActionFor' call for a checkout operation takes 2 mandatory
    arguments, 'dest_container', 'initial_transition' and an optional
    'language_map'. The first two are similar to what happens for
    publishing, and 'language_map' is a mapping of new languages to old
    languages, used to specify what languages will appear in the checked
    out document and what language they are based on. This can be used
    to checkout a version into a new language for translation. If
    'language_map' is not present, then all languages are copied.

    The 'doActionFor' call for a checkin operation takes 2 arguments,
    'dest_objects' and 'checkin_transition'. They describe the
    destination objects into which to merge changes, and the checkin
    transition the destination objects will follow after changes are
    merged.

    Note that after a checkin the working document is deleted.

  Global history

    Because documents can now have several related versions in several
    locations, it is useful to be able to get a global history of all
    workflow operations that applied to all revisions of a docid. This
    history cannot be stored in the proxies themselves because the
    proxies may very well be deleted in the normal course of operations,
    and we still want to keep their history.

    To solve this, the worklow tool now has a getFullHistoryOf() method,
    that returns the full history. The full history is actually stored
    in the repository tool.

  Document lifecycle

    This is an attempt to describe the lifecycle of a document. It
    assumes a site set up with two areas, one which is the workspaces,
    with folders of portal_type Workspace, where authors create and
    modify content, and one area which is the hierarchical public
    sections, where folders have portal_type Section.

    There is a workspace document workflow (actually one for each
    content portal_type), which describes the workflow followed by
    documents when they are being worked upon.

    There is a section document workflow (for each portal_type), which
    describes the fact that documents go through a submission process
    before being published.

    There is a workflow for Section themeselves, which permits the
    versionning of the changes to a section's title and description.

3) Stack workflows

   XXX to be continued
