from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from pages.base_page import BasePage
import time

class InitPage(BasePage):

    FISSC_BTN = (By.ID, "Logon_PopupActions_Menu_DXI0_T")
    CANCEL_BTN= (By.ID, "Logon_PopupActions_Menu_DXI1_T")
    TABLA = (By.CSS_SELECTOR, "table[id*='dviFiscalizacionEmpresaDTs']")
    INPUT_NOMBRE_EMP = (By.CSS_SELECTOR, "input[name*='dviEmpresaAFiscalizarNombre_Edit_dropdown$DD']")
    INPUT_RUT_EMP = (By.CSS_SELECTOR, "input[id*='dviEmpresaAFiscalizarRUT_Edit_dropdown_DD_I']")
    CONFIRM_BTN =(By.ID, "Logon_PopupActions_Menu_DXI0_T")

    def seleccionar_empresa_por_rut(self, rut):
        self.wait_for_visible(self.TABLA)
        opcion = (By.XPATH, f"//td[contains(text(), '{rut}')]")
        time.sleep(3)
        self.wait_and_click(opcion)
        self.wait_loader()

    def log_out(self):
        self.wait_and_click(self.CANCEL_BTN)

    def fisc_init(self):
        self.wait_and_click(self.FISSC_BTN)
        self.wait_loader()
    
    def confirmar_empresa(self, rut):
        element = (By.XPATH, f"//span[contains(text(), '{rut}')]")
        try:
            self.wait_for_visible(element)
            return True
        except:
            return False

    def confirm(self):
        self.wait_and_click(self.CONFIRM_BTN)
        self.wait_loader()
    
    def validar_autocompletado(self, rut):
        self.seleccionar_empresa_por_rut(rut)

        nombre_valor = self.wait_for_visible(self.INPUT_NOMBRE_EMP).get_attribute("value")
        rut_valor = self.wait_for_visible(self.INPUT_RUT_EMP).get_attribute("value")

        return nombre_valor == rut_valor

    def is_error_user_displayed(self):
        return self.driver.find_element(By.XPATH, "//div[contains(@class, 'dx-toast-message') and contains(text(), 'El usuario indicado no es valido')]").is_displayed()

    