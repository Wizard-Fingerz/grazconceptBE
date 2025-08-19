from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import UserPermissions, Roles, Modules
import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=UserPermissions)
def add_permission_to_SuperAdmin(sender, instance, created, **kwargs):
    if created:
        try:
            SuperAdmin_role = Roles.objects.get(name='SuperAdmin')
            # Iterate through all modules associated with the SuperAdmin role
            for module in SuperAdmin_role.modules.all():
                # Add the new permission to each module's permissions
                module.permissions.add(instance)
            logger.info(f"Added permission {instance.name} to SuperAdmin role")
        except Roles.DoesNotExist:
            logger.warning("SuperAdmin role does not exist")
            pass


@receiver(post_migrate)
def create_SuperAdmin_role(sender, **kwargs):
    # Check if the sender is the correct app
    if sender.name == 'app':  # Replace with your actual app name
        role_name = 'SuperAdmin'
        
        # Create the SuperAdmin role
        role, created = Roles.objects.get_or_create(
            name=role_name,
            defaults={'is_active': True}
        )
        
        if created:
            logger.info(f"Created SuperAdmin role: {role_name}")
        else:
            logger.info(f"SuperAdmin role already exists: {role_name}")
        
        # Retrieve all permissions and add them to the SuperAdmin role
        #all_permissions = UserPermissions.objects.all()
        all_modules = Modules.objects.all()
        
        for module in all_modules:
            role.modules.add(module)
            logger.info(f"Added module {module.name} to SuperAdmin role")


@receiver(post_migrate)
def setup_permissions_and_modules(sender, **kwargs):
    """
    Signal handler to create modules (if necessary) and map permissions after migrations.
    Prints messages to the console and logs them.
    """
    if sender.name == 'app':  # Replace with your app's name
        # print("Setting up modules and permissions after migration...")
        logger.info("Setting up modules and permissions after migration...")

        # Step 1: Fetch all modules from the database
        modules = Modules.objects.all()
        if not modules.exists():
            # print("No modules found in the database. Skipping permission mapping.")
            #logger.warning("No modules found in the database. Skipping permission mapping.")
            return

        # Step 2: Map permissions to modules
        for permission in UserPermissions.objects.all():
            
            try:
                permission_name = permission.name.lower()

                # Define keyword mappings
                keyword_mappings = {
                    'Accounting': ['payment', 'balance', 'account', 'bills', 'journal', 'ledger', 'expenses', 'fiscal', 'credit', 'invoice', 'deposit'],
                    'Investigations': ['test', 'lab', 'laboratory', 'examinations'],
                    'Wallet': ['wallet'],
                    'Cycles': ['lmp', 'cycle', 'mens', 'baseline', 'allergies', 'monitor', 'fish', 'indicator', 'complication'],
                    'Tasks': ['tasks', 'task'],
                    'QMS': ['documents', 'incidents'],
                    'ART': ['inventory', 'embryo', 'sperm', 'oocyte', 'fullcryo', 'equipments'],
                    'Patients': ['case', 'communication', 'vitals']
                }

                # Find module based on keywords
                module_name = None
                for key, keywords in keyword_mappings.items():
                    if any(keyword in permission_name for keyword in keywords):
                        module_name = key
                        break

                # Default to "Settings" if no match is found
                if not module_name:
                    module_name = "Settings"
                    #logger.warning(f"No keyword match found for permission '{permission.name}', assigning to 'Settings'.")

                # Get module instance
                module, created = Modules.objects.get_or_create(name=module_name)

                # Assign permission
                module.permissions.add(permission)
                logger.info(f"Mapped permission '{permission.name}' to module '{module.name}'")

            except Exception as e:
                logger.error(f"Error mapping permission '{permission.name}' to module: {str(e)}")

